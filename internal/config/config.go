package config

import (
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	Env                string
	HTTPAddr           string
	PostgresDSN        string
	RedisAddr          string
	DataDir            string
	LayoutServiceURL   string
	OCRServiceURL      string
	VectorServiceURL   string
	ExportServiceURL   string
	MockPipeline       bool
	MaxParallelJobs    int
	GPUSemaphoreKey    string
	GPULockTTL         time.Duration
	AllowedOrigins     []string
	MCPAllowedHosts    []string
	SessionSecret      string
	LogLevel           string
	ProfileGPU         string
	TileSize           int
	MaxImageSide       int
	FP16Enabled        bool
	OCRBatchSize       int
	LayoutBatchSize    int
	OCRUseGPU          bool
	LayoutUseGPU       bool
	MaxGPUTasks          int
	RequestTimeout     time.Duration
	ModelCacheDir      string
	ModelAutoDownload  bool
	ModelStartupStrict bool
}

func getenv(key, def string) string {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	return v
}

func getenvInt(key string, def int) int {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return n
}

func getenvBool(key string, def bool) bool {
	v := strings.ToLower(strings.TrimSpace(os.Getenv(key)))
	if v == "" {
		return def
	}
	return v == "1" || v == "true" || v == "yes"
}

func getenvDuration(key string, def time.Duration) time.Duration {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	d, err := time.ParseDuration(v)
	if err != nil {
		return def
	}
	return d
}

func splitCSV(s string) []string {
	if strings.TrimSpace(s) == "" {
		return nil
	}
	parts := strings.Split(s, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

func Load() Config {
	return Config{
		Env:              getenv("APP_ENV", "development"),
		HTTPAddr:         getenv("HTTP_ADDR", ":8080"),
		PostgresDSN:      getenv("POSTGRES_DSN", "postgres://drawdigit:drawdigit@localhost:5432/drawdigit?sslmode=disable"),
		RedisAddr:        getenv("REDIS_ADDR", "localhost:6379"),
		DataDir:          getenv("DATA_DIR", "./data"),
		LayoutServiceURL: getenv("LAYOUT_SERVICE_URL", "http://localhost:8001"),
		OCRServiceURL:    getenv("OCR_SERVICE_URL", "http://localhost:8002"),
		VectorServiceURL: getenv("VECTOR_SERVICE_URL", "http://localhost:8003"),
		ExportServiceURL: getenv("EXPORT_SERVICE_URL", "http://localhost:8004"),
		MockPipeline:     getenvBool("MOCK_PIPELINE", false),
		MaxParallelJobs:  getenvInt("MAX_PARALLEL_JOBS", 2),
		GPUSemaphoreKey:  getenv("GPU_SEMAPHORE_KEY", "gpu:global_lock"),
		GPULockTTL:       getenvDuration("GPU_LOCK_TTL", 30*time.Minute),
		AllowedOrigins:   splitCSV(getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")),
		MCPAllowedHosts:  splitCSV(getenv("MCP_ALLOWED_HOSTS", "localhost,127.0.0.1")),
		SessionSecret:    getenv("SESSION_SECRET", "dev-change-me-in-production"),
		LogLevel:         getenv("LOG_LEVEL", "info"),
		ProfileGPU:       getenv("PROFILE_GPU", "PROFILE_GPU_12GB"),
		TileSize:         getenvInt("TILE_SIZE", 512),
		MaxImageSide:     getenvInt("MAX_IMAGE_SIDE", 2048),
		FP16Enabled:      getenvBool("FP16_ENABLED", true),
		OCRBatchSize:     getenvInt("OCR_BATCH_SIZE", 1),
		LayoutBatchSize:  getenvInt("LAYOUT_BATCH_SIZE", 1),
		OCRUseGPU:        getenvBool("OCR_USE_GPU", true),
		LayoutUseGPU:     getenvBool("LAYOUT_USE_GPU", true),
		MaxGPUTasks:      getenvInt("MAX_GPU_TASKS", 1),
		RequestTimeout:   getenvDuration("HTTP_CLIENT_TIMEOUT", 120*time.Second),
		ModelCacheDir:    getenv("MODEL_CACHE_DIR", "/models_cache"),
		ModelAutoDownload: getenvBool("MODEL_AUTO_DOWNLOAD", true),
		ModelStartupStrict: getenvBool("MODEL_STARTUP_STRICT", true),
	}
}
