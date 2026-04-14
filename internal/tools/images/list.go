package images

import (
	"os"
	"path/filepath"
	"strings"
)

var exts = map[string]struct{}{
	".jpg": {}, ".jpeg": {}, ".png": {}, ".tif": {}, ".tiff": {},
}

func IsImage(name string) bool {
	ext := strings.ToLower(filepath.Ext(name))
	_, ok := exts[ext]
	return ok
}

func ListRecursive(root string) ([]string, error) {
	var out []string
	err := filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		if IsImage(path) {
			out = append(out, path)
		}
		return nil
	})
	return out, err
}
