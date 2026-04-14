package queue

import (
	"context"
	"encoding/json"
	"time"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

const defaultQueueKey = "jobs:queue"

type Client struct {
	rdb *redis.Client
	key string
}

func New(addr, key string) *Client {
	if key == "" {
		key = defaultQueueKey
	}
	rdb := redis.NewClient(&redis.Options{Addr: addr})
	return &Client{rdb: rdb, key: key}
}

func (c *Client) RDB() *redis.Client { return c.rdb }

type JobMessage struct {
	JobID uuid.UUID `json:"job_id"`
}

func (c *Client) Enqueue(ctx context.Context, jobID uuid.UUID) error {
	b, err := json.Marshal(JobMessage{JobID: jobID})
	if err != nil {
		return err
	}
	return c.rdb.LPush(ctx, c.key, string(b)).Err()
}

func (c *Client) BlockingPop(ctx context.Context, timeout time.Duration) (*JobMessage, error) {
	res, err := c.rdb.BRPop(ctx, timeout, c.key).Result()
	if err == redis.Nil {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if len(res) < 2 {
		return nil, nil
	}
	var m JobMessage
	if err := json.Unmarshal([]byte(res[1]), &m); err != nil {
		return nil, err
	}
	return &m, nil
}
