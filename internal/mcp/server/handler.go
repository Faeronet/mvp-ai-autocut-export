package server

import (
	"encoding/json"
	"io"
	"net/http"

	"github.com/drawdigit/mvp/internal/mcp/resources"
	"github.com/drawdigit/mvp/internal/mcp/schemas"
	"github.com/drawdigit/mvp/internal/mcp/prompts"
	"github.com/drawdigit/mvp/internal/mcp/session"
	"github.com/drawdigit/mvp/internal/mcp/tools"
	"github.com/drawdigit/mvp/internal/mcp/transport"
)

type Handler struct {
	Sessions   *session.Store
	Executor   *tools.Executor
	Resources  *resources.Resolver
	AllowHosts []string
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if !transport.ValidateOrigin(r, h.AllowHosts) {
		http.Error(w, "forbidden origin", http.StatusForbidden)
		return
	}
	ver := r.Header.Get(transport.ProtocolVersionHeader)
	if ver == "" {
		ver = transport.DefaultProtocolVersion
	}
	sid := r.Header.Get(transport.SessionHeader)
	sessionID := h.Sessions.Ensure(sid)
	w.Header().Set(transport.SessionHeader, sessionID)
	w.Header().Set(transport.ProtocolVersionHeader, ver)

	body, _ := io.ReadAll(r.Body)
	var req transport.Request
	if err := json.Unmarshal(body, &req); err != nil {
		writeRPCError(w, nil, -32700, "parse error")
		return
	}
	res := h.dispatch(r, &req, ver)
	b, _ := json.Marshal(res)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(b)
}

func (h *Handler) dispatch(r *http.Request, req *transport.Request, ver string) transport.Response {
	switch req.Method {
	case "initialize":
		return transport.Response{
			JSONRPC: "2.0", ID: req.ID,
			Result: map[string]any{
				"protocolVersion": ver,
				"capabilities": map[string]any{
					"tools":     map[string]any{},
					"resources": map[string]any{},
					"prompts":   map[string]any{},
				},
				"serverInfo": map[string]any{"name": "drawdigit-mcp", "version": "0.1.0"},
			},
		}
	case "tools/list":
		return transport.Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"tools": schemas.ToolList()}}
	case "tools/call":
		var p tools.CallParams
		_ = json.Unmarshal(req.Params, &p)
		out, err := h.Executor.Call(r.Context(), p.Name, p.Arguments)
		if err != nil {
			return transport.Response{JSONRPC: "2.0", ID: req.ID, Error: &transport.RPCError{Code: -32000, Message: err.Error()}}
		}
		return transport.Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"content": []map[string]any{{"type": "text", "text": mustJSON(out)}}}}
	case "resources/list":
		return transport.Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"resources": resources.List()}}
	case "resources/read":
		var p struct {
			URI string `json:"uri"`
		}
		_ = json.Unmarshal(req.Params, &p)
		res, err := h.Resources.Read(r.Context(), p.URI)
		if err != nil {
			return transport.Response{JSONRPC: "2.0", ID: req.ID, Error: &transport.RPCError{Code: -32002, Message: "not found"}}
		}
		return transport.Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"contents": []map[string]any{{"uri": res.URI, "mimeType": res.Mime, "text": res.Content}},
		}}
	case "prompts/list":
		return transport.Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"prompts": prompts.List()}}
	case "prompts/get":
		var p struct {
			Name string `json:"name"`
		}
		_ = json.Unmarshal(req.Params, &p)
		text, ok := prompts.Get(p.Name)
		if !ok {
			return transport.Response{JSONRPC: "2.0", ID: req.ID, Error: &transport.RPCError{Code: -32000, Message: "unknown prompt"}}
		}
		return transport.Response{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"description": "prompt",
			"messages": []map[string]any{{"role": "user", "content": map[string]any{"type": "text", "text": text}}},
		}}
	default:
		return transport.Response{JSONRPC: "2.0", ID: req.ID, Error: &transport.RPCError{Code: -32601, Message: "method not found"}}
	}
}

func writeRPCError(w http.ResponseWriter, id json.RawMessage, code int, msg string) {
	res := transport.Response{JSONRPC: "2.0", ID: id, Error: &transport.RPCError{Code: code, Message: msg}}
	b, _ := json.Marshal(res)
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set(transport.ProtocolVersionHeader, transport.DefaultProtocolVersion)
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(b)
}

func mustJSON(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}
