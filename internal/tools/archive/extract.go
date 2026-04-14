package archive

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/drawdigit/mvp/internal/storage"
	"github.com/drawdigit/mvp/pkg/apperrors"
)

// Extract unpacks archivePath into destDir. Supports zip via unzip, 7z/rar via external tools if present.
func Extract(ctx context.Context, archivePath, destDir string) error {
	if err := storage.EnsureDir(destDir); err != nil {
		return err
	}
	ext := strings.ToLower(filepath.Ext(archivePath))
	switch ext {
	case ".zip":
		if err := UnzipNative(archivePath, destDir); err != nil {
			return apperrors.Wrap(apperrors.KindPipeline, "extract_failed", "zip extraction failed", err)
		}
		return nil
	case ".7z":
		return run(ctx, "7z", "x", "-y", "-o"+destDir, archivePath)
	case ".rar":
		if HasTool("unar") {
			if err := run(ctx, "unar", "-o", destDir, archivePath); err != nil {
				if hasAnyImage(destDir) {
					return nil
				}
				return err
			}
			return nil
		}
		if err := run(ctx, "unrar", "x", "-o+", archivePath, destDir+"/"); err != nil {
			if hasAnyImage(destDir) {
				return nil
			}
			return err
		}
		return nil
	default:
		return apperrors.New(apperrors.KindUnsupported, "unsupported_archive", "unsupported archive format (use zip, 7z, or rar)")
	}
}

func hasAnyImage(dir string) bool {
	exts := map[string]struct{}{
		".png":  {},
		".jpg":  {},
		".jpeg": {},
		".tif":  {},
		".tiff": {},
		".bmp":  {},
		".webp": {},
	}
	found := false
	_ = filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d == nil || d.IsDir() {
			return nil
		}
		if _, ok := exts[strings.ToLower(filepath.Ext(path))]; ok {
			found = true
			return filepath.SkipAll
		}
		return nil
	})
	return found
}

func run(ctx context.Context, name string, args ...string) error {
	cmd := exec.CommandContext(ctx, name, args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return apperrors.Wrap(apperrors.KindPipeline, "extract_failed", string(out), err)
	}
	return nil
}

// HasTool returns true if binary exists in PATH.
func HasTool(name string) bool {
	_, err := exec.LookPath(name)
	return err == nil
}

func ValidateExtractor(ext string) error {
	switch strings.ToLower(ext) {
	case ".zip":
		return nil
	case ".7z":
		if !HasTool("7z") && !HasTool("7za") {
			return fmt.Errorf("7z not installed")
		}
	case ".rar":
		if !HasTool("unrar") && !HasTool("unar") {
			return fmt.Errorf("unrar not installed")
		}
	default:
		return apperrors.New(apperrors.KindUnsupported, "unsupported_archive", "unsupported archive format")
	}
	return nil
}
