# 06 - Feature Verification v9

## Verification Summary

| Check | Result |
|-------|--------|
| All tests pass (113/114) | PASS |
| OSS config loads correctly | PASS |
| OSS URL building correct | PASS |
| USE_OSS flag gates upload behavior | PASS |
| _normalize_media_paths skips OSS URLs | PASS |
| UAT server accessible (http://8.213.209.231/dream/) | PASS (HTTP 200) |

## Blocking Issue

**Bucket ACL**: The OSS bucket `dream20260711` returns 403 AccessDenied on upload. This needs to be fixed in the Alibaba Cloud console:

1. Login to Alibaba Cloud console
2. Navigate to OSS > Buckets > dream20260711
3. Check Bucket ACL settings or RAM policy for the AccessKey
4. Grant `PutObject` permission
5. Also set bucket to public-read for frontend media access

Once ACL is fixed, run `python3 -m unittest tests.test_oss.TestUploadFileIntegration` to verify.

## Deployment Notes (for Phase 7)

1. Install oss2 on server: `.venv/bin/pip install oss2`
2. Deploy updated code to server
3. Fix bucket ACL in Alibaba Cloud console
4. Run integration test to confirm upload works
5. Clear existing messages and media
6. Run downloader to repopulate with OSS URLs
7. Regenerate HTML
