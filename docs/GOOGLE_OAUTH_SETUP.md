# Google OAuth Setup Guide

## Overview
This guide explains how to enable Google OAuth authentication for the Resee platform.

## Prerequisites
- Google Cloud Console account
- Access to environment variables (.env file)

## Setup Steps

### 1. Google Cloud Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Web application" as the application type
4. Configure the OAuth consent screen if prompted
5. Add the following to your OAuth client:

   **Authorized JavaScript origins:**
   - `http://localhost:3000` (for development)
   - `https://reseeall.com` (for production)
   - `https://www.reseeall.com` (for production)

   **Authorized redirect URIs:**
   - `http://localhost:3000` (for development)
   - `https://reseeall.com` (for production)
   - `https://www.reseeall.com` (for production)

6. Click "Create" and save the Client ID and Client Secret

### 3. Configure Environment Variables

#### Development (.env)
```bash
# Frontend Google OAuth
REACT_APP_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com

# Backend Google OAuth (same Client ID)
GOOGLE_OAUTH2_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret-here
```

#### Production (.env.prod)
```bash
# Frontend Google OAuth
REACT_APP_GOOGLE_CLIENT_ID=your-production-client-id.apps.googleusercontent.com

# Backend Google OAuth
GOOGLE_OAUTH2_CLIENT_ID=your-production-client-id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=your-production-client-secret
```

### 4. Restart Services

After updating environment variables:

```bash
# Development
docker-compose restart

# Production
docker-compose --env-file .env.prod restart
```

## Features

When Google OAuth is properly configured:

1. **Login Page**: Users can sign in with their Google account
2. **Register Page**: New users can sign up using Google
3. **Automatic Email Verification**: Google accounts are automatically verified
4. **Profile Data**: User's name is populated from Google profile

## Troubleshooting

### Google button not appearing
- Check that `REACT_APP_GOOGLE_CLIENT_ID` is set in the environment
- Verify the frontend container has been restarted
- Check browser console for any errors

### Authentication fails
- Verify the Client ID matches between frontend and backend
- Check that the domain is added to authorized origins
- Ensure Google+ API is enabled in Google Cloud Console
- Check backend logs: `docker-compose logs backend`

### Invalid client error
- Verify the Client Secret is correct (backend only)
- Check that the Client ID format is correct (ends with .apps.googleusercontent.com)

## Security Notes

1. **Never commit credentials**: Keep Client ID and Secret out of version control
2. **Use different credentials**: Use separate OAuth clients for development and production
3. **Monitor usage**: Regularly check Google Cloud Console for unusual activity
4. **Rotate secrets**: Periodically rotate the Client Secret for security

## Disabling Google OAuth

To disable Google OAuth, simply leave the environment variables empty:

```bash
REACT_APP_GOOGLE_CLIENT_ID=
GOOGLE_OAUTH2_CLIENT_ID=
GOOGLE_OAUTH2_CLIENT_SECRET=
```

The Google sign-in button will automatically be hidden when the Client ID is not configured.