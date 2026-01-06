# 🔧 Common Issues & Quick Fixes

Quick solutions for common problems.

---

## 🚨 Backend Issues

### Backend won't start

**Symptoms**: App crashes on DigitalOcean, logs show errors

**Solutions**:

1. Check logs in DigitalOcean dashboard
2. Verify environment variables are set:
   ```
   PORT=8000
   ENVIRONMENT=production
   ```
3. Check `requirements.txt` - ensure boto3 is listed
4. Try redeploying from scratch

**Fix**:

```bash
# Update requirements and redeploy
git add backend/requirements.txt
git commit -m "Fix dependencies"
git push
```

### "Module not found" errors

**Symptoms**: ImportError in logs

**Solution**: Add missing package to `requirements.txt`:

```
pip freeze | grep <package_name>
# Add to requirements.txt
git push
```

### Health check failing

**Symptoms**: App keeps restarting

**Solutions**:

1. Increase health check initial delay to 60 seconds
2. Check `/api/health` endpoint manually
3. Review startup logs

---

## 🌐 Frontend Issues

### "Cannot connect to backend"

**Symptoms**: Network errors, CORS errors

**Solutions**:

1. Verify `NEXT_PUBLIC_API_URL` is correct in Vercel
2. Check it includes `https://` and no trailing slash
3. Update backend CORS to include frontend URL:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```

### Environment variable not working

**Symptoms**: Still using localhost

**Fix in Vercel**:

1. Go to Settings → Environment Variables
2. Add: `NEXT_PUBLIC_API_URL=https://your-backend.ondigitalocean.app`
3. Redeploy (Deployments → Click ••• → Redeploy)

### Build failing

**Symptoms**: Vercel deployment fails

**Solutions**:

1. Check build logs in Vercel dashboard
2. Run `npm run build` locally to test
3. Fix TypeScript errors
4. Ensure all dependencies in `package.json`

---

## 🔒 Rate Limiting Issues

### "Too many requests" error

**Symptoms**: 429 status code

**Solutions**:

1. **Normal**: Wait and try again
2. **For testing**: Temporarily increase limits in `backend/app/middleware/rate_limiter.py`:
   ```python
   max_requests=120  # Double to 120/min
   max_uploads=10    # Double to 10/10min
   ```

### Need different limits per user

**Current**: All users share same limits (IP-based)

**Future enhancement**: Add API keys for authenticated users with higher limits

---

## 📁 File Upload Issues

### "File too large" error

**Symptoms**: Upload rejected

**Solutions**:

1. **Normal**: File > 50MB, compress or split PDF
2. **Increase limit** (not recommended): Edit `backend/app/utils/validators.py`:
   ```python
   MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
   ```

### "Too many pages" error

**Symptoms**: PDF rejected

**Solutions**:

1. **Normal**: PDF > 100 pages, split document
2. **Increase limit**: Edit `backend/app/utils/validators.py`:
   ```python
   HARD_PAGE_LIMIT = 200  # 200 pages
   ```

### Upload hangs

**Symptoms**: Upload never completes

**Solutions**:

1. Check internet connection
2. Try smaller file
3. Check backend logs for errors
4. Verify DigitalOcean app is running

---

## 🎤 Voice Recognition Issues

### Voice not working

**Symptoms**: "Speech recognition not supported"

**Solutions**:

1. **Use Chrome or Edge** (best support)
2. Grant microphone permissions
3. Use HTTPS (required for voice)
4. **Alternative**: Use text input instead

### Voice not detected

**Symptoms**: No transcription shown

**Solutions**:

1. Check microphone is working
2. Speak clearly and wait for response
3. Check browser permissions
4. Try text input as backup

---

## ☁️ R2 Storage Issues (Optional)

### R2 not working

**Symptoms**: Files still using local storage

**Check**:

1. Verify all R2 env vars are set:
   ```
   R2_ACCOUNT_ID=xxx
   R2_ACCESS_KEY_ID=xxx
   R2_SECRET_ACCESS_KEY=xxx
   R2_BUCKET_NAME=voice-pdf-files
   ```
2. Check bucket exists in Cloudflare
3. Verify API tokens are correct
4. Check backend logs for R2 errors

**Fallback**: If R2 fails, app automatically uses local storage

---

## 🗄️ Database Issues

### jobs.db file growing too large

**Symptoms**: Disk space issues

**Solutions**:

1. **Auto-cleanup** runs every 7 days
2. **Manual cleanup**: Reduce retention in `backend/app/utils/job_tracker.py`:
   ```python
   cleanup_old_jobs(days=3)  # 3 days instead of 7
   ```

### Database locked error

**Symptoms**: SQLite lock errors

**Solution**: Restart backend (rare issue, SQLite is single-threaded)

---

## 🚀 Performance Issues

### Slow processing

**Symptoms**: Takes too long to process

**Causes**:

1. Large PDF (many pages)
2. High server load
3. Cold start (first request)

**Solutions**:

1. **Expected** for 50+ page PDFs
2. Upgrade DigitalOcean plan (Basic → Professional)
3. Wait 30s for cold start, then fast

### Out of memory

**Symptoms**: Backend crashes during processing

**Solutions**:

1. Process smaller PDFs
2. Upgrade DigitalOcean plan (more RAM)
3. Check for memory leaks in logs

---

## 🌍 CORS Errors

### Browser shows CORS error

**Symptoms**: "Access-Control-Allow-Origin" error in console

**Fix**:

1. Add frontend URL to backend CORS
2. In DigitalOcean, add environment variable:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```
3. Or update `backend/app/main.py`:
   ```python
   allow_origins=[
       "https://your-app.vercel.app",
       "http://localhost:3000"
   ]
   ```
4. Redeploy backend

---

## 📱 Mobile Issues

### Voice not working on mobile

**Symptoms**: No microphone access

**Solutions**:

1. **iOS**: Use Safari (Chrome voice API limited)
2. **Android**: Use Chrome
3. **Always**: Use text input alternative

### Upload button not working

**Symptoms**: Can't select file

**Solution**: Mobile browsers are supported, try:

1. Update browser to latest version
2. Grant file access permissions
3. Use desktop for large files

---

## 🔄 Deployment Issues

### DigitalOcean build failing

**Symptoms**: "Build failed" error

**Check**:

1. `requirements.txt` syntax correct
2. Python version compatible (3.11+)
3. All imports resolve
4. No circular dependencies

**Fix**:

```bash
# Test locally first
cd backend
pip install -r requirements.txt
python -c "from app.main import app"
```

### Vercel build failing

**Symptoms**: Build errors in Vercel

**Check**:

1. `npm run build` works locally
2. TypeScript errors resolved
3. All dependencies in `package.json`

**Fix**:

```bash
# Test locally
npm run build
# Fix errors, then push
git push
```

---

## 🧪 Testing Issues

### Can't test locally

**Symptoms**: Backend won't start

**Solutions**:

1. Create virtual environment:
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. Check port 8000 is free
3. Run: `python run.py server`

### Frontend can't connect to local backend

**Symptoms**: CORS errors locally

**Fix**: Backend already allows `localhost:3000` in CORS

---

## 🆘 Emergency Fixes

### Everything broken, need to rollback

**DigitalOcean**:

1. Go to app → Deployments
2. Click previous successful deployment
3. Click "Redeploy"

**Vercel**:

1. Go to Deployments
2. Find previous working deployment
3. Click ••• → Promote to Production

### Need to start fresh

1. Delete DigitalOcean app
2. Delete Vercel project
3. Follow [QUICK_DEPLOY.md](./QUICK_DEPLOY.md) again

---

## 📊 Monitoring & Debugging

### Check if backend is healthy

```bash
curl https://your-backend.ondigitalocean.app/api/health
```

Expected: `{"status":"healthy",...}`

### View backend logs

- DigitalOcean: App → Runtime Logs
- Filter by error level

### View frontend logs

- Vercel: Project → Logs
- Browser: F12 → Console

### Check rate limit status

- No direct endpoint (privacy)
- Check logs for "Rate limit exceeded" warnings

---

## 🔍 Still Having Issues?

### Check These First:

1. ✅ Backend health endpoint works
2. ✅ Frontend loads without errors
3. ✅ Environment variables are correct
4. ✅ CORS is configured
5. ✅ No errors in browser console

### Get Help:

- **DigitalOcean**: https://www.digitalocean.com/support
- **Vercel**: https://vercel.com/support
- **Cloudflare**: https://support.cloudflare.com

### Debug Locally:

```bash
# Test backend
cd backend
venv\Scripts\activate
python run.py server
# Visit http://localhost:8000/docs

# Test frontend
npm run dev
# Visit http://localhost:3000
```

---

## ✅ Prevention Tips

1. **Always test locally first** before deploying
2. **Read logs** when something fails
3. **Check environment variables** are set correctly
4. **Keep backups** of working configurations
5. **Monitor health endpoint** regularly
6. **Stay within limits** to avoid errors

---

**Most issues are configuration-related!**

Double-check:

- ✅ Environment variables
- ✅ CORS settings
- ✅ API URL in frontend
- ✅ Deployment logs

Happy debugging! 🐛
