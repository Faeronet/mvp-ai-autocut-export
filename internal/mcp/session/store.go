package session

import (
	"sync"

	"github.com/google/uuid"
)

type Store struct {
	mu    sync.RWMutex
	ids   map[string]struct{}
}

func NewStore() *Store {
	return &Store{ids: map[string]struct{}{}}
}

func (s *Store) New() string {
	id := uuid.New().String()
	s.mu.Lock()
	s.ids[id] = struct{}{}
	s.mu.Unlock()
	return id
}

func (s *Store) Valid(id string) bool {
	if id == "" {
		return false
	}
	s.mu.RLock()
	defer s.mu.RUnlock()
	_, ok := s.ids[id]
	return ok
}

func (s *Store) Ensure(id string) string {
	if id != "" && s.Valid(id) {
		return id
	}
	return s.New()
}
