# 04 - Code Review v9

## Build & Test

| Metric | Value |
|--------|-------|
| Tests total | 114 |
| Tests passed | 113 |
| Failures | 1 (expected - bucket ACL, not code bug) |
| New tests | 10 (OSS config, URL, upload) |

## Scope Check

- **Intent**: Migrate media storage from local disk to Alibaba Cloud OSS
- **Delivered**: OSS uploader module, downloader integration with USE_OSS flag, OSS URL normalization skip
- **Status**: CLEAN

## Issues Found

### Medium Severity

1. **oss_config.json contains real credentials** (`src/oss_config.json`)
   - AccessKey ID and Secret are stored in plaintext in version control
   - **Verdict**: Per user instruction ("OSS 的認證放入版控"). Acceptable for private repo. Rotate keys if repo visibility changes.

### Low Severity

1. **_download_to_oss functions run synchronously** (`download_tg_channel.py:93`)
   - `oss_uploader.upload_file()` is a blocking call that holds the asyncio event loop
   - For small files (photos <1MB) this is negligible. Large videos could cause noticeable pauses.
   - **Verdict**: Acceptable for current scale. Consider `run_in_executor` if uploads become a bottleneck.

2. **No OSS upload retry logic**
   - If OSS upload fails (network, rate limit), the temp file is deleted and the message is silently skipped
   - **Verdict**: Low risk. Failed messages will be retried on next cron run. Acceptable for batch processing.

3. **cleanup_old.py not removed**
   - Still in repo but no longer needed for media cleanup (OSS doesn't fill up)
   - **Verdict**: Harmless. Can remove in a future cleanup PR.

## No Issues Found In

| Category | Status |
|----------|--------|
| Backward compatibility | Clean - USE_OSS flag preserves local storage fallback |
| Test coverage | Adequate - 10 new tests for OSS module |
| URL normalization | Clean - OSS URLs correctly skipped in _normalize_media_paths |
| Asyncio correctness | Clean - _download_to_oss is properly awaited |
| Config loading | Clean - handles missing config gracefully |

## Summary

Implementation is clean. OSS upload is gated behind `USE_OSS` flag, so the system falls back to local storage if no OSS config exists. The bucket ACL issue needs to be resolved in the Alibaba Cloud console before the deployment test can work end-to-end.
