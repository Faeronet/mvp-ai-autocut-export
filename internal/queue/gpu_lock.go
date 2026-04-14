package queue

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"time"

	"github.com/redis/go-redis/v9"
)

// GPULock is a distributed mutex for sequential GPU scheduling (default MAX_GPU_TASKS=1).
type GPULock struct {
	rdb   *redis.Client
	key   string
	ttl   time.Duration
	token string
}

func NewGPULock(rdb *redis.Client, key string, ttl time.Duration) *GPULock {
	return &GPULock{rdb: rdb, key: key, ttl: ttl}
}

func (g *GPULock) randomToken() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

// Acquire blocks until lock acquired or ctx done.
func (g *GPULock) Acquire(ctx context.Context) error {
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	for {
		token := g.randomToken()
		ok, err := g.rdb.SetNX(ctx, g.key, token, g.ttl).Result()
		if err != nil {
			return err
		}
		if ok {
			g.token = token
			return nil
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
		}
	}
}

func (g *GPULock) Release(ctx context.Context) error {
	if g.token == "" {
		return nil
	}
	script := redis.NewScript(`
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		end
		return 0
	`)
	return script.Run(ctx, g.rdb, []string{g.key}, g.token).Err()
}

func (g *GPULock) IsHeld(ctx context.Context) (bool, error) {
	v, err := g.rdb.Exists(ctx, g.key).Result()
	if err != nil {
		return false, err
	}
	return v > 0, nil
}
