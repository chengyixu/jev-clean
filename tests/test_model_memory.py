"""MLX keeps freed GPU buffers in a cache whose default limit is about the size of RAM.

Real resources produce model inputs of many different lengths, so freed buffers rarely match the
next request and the cache only grows: measured +1.3 GB per judgment until the scan reached
tens of GB and macOS jetsam killed the system. The loaded model must run with no buffer cache.
"""

import sys
import types

import mlx.core as mx

from jev_clean.infrastructure import model


def test_loaded_model_runs_without_an_mlx_buffer_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(model.LayaAdvisor, "_shared", None)
    monkeypatch.setattr(model, "prepare_checkpoint", lambda: tmp_path)
    monkeypatch.setitem(sys.modules, "laya_mlx", types.SimpleNamespace(load=lambda path: object()))
    monkeypatch.setattr(model, "load_cleanup_adapter", lambda backend: None)
    default = mx.set_cache_limit(64 * 2**30)  # an unbounded-looking limit, like the MLX default
    try:
        model.LayaAdvisor().load()
        assert mx.set_cache_limit(default) == 0
    finally:
        mx.set_cache_limit(default)
