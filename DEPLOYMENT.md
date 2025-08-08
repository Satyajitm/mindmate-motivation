# MindMate Voice Assistant - Deployment Guide

This guide will walk you through deploying the MindMate Voice Assistant to a cloud platform. We'll cover deployment to Render, but the process is similar for other platforms.

## Prerequisites

1. A GitHub account
2. A Render/Heroku/Azure account (free tier available)
3. An OpenAI API key

## Deployment Options

### Option 1: Deploy to Render (Recommended)

1. **Prepare your repository**
   - Push your code to a GitHub repository
   - Ensure all dependencies are in `backend/requirements.txt`

2. **Create a new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" and select "Web Service"
   - Connect your GitHub repository

3. **Configure the service**
   - Name: `mindmate-voice-assistant` (or your preferred name)
   - Region: Choose the closest to your users
   - Branch: `main` (or your preferred branch)
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PYTHON_VERSION`: `3.9` (or your Python version)
   - `PORT`: `10000` (or your preferred port)

5. **Deploy**
   - Click "Create Web Service"
   - Wait for the build to complete
   - Your app will be live at `https://your-app-name.onrender.com`

### Option 2: Deploy to Heroku

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Windows
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create a new Heroku app**
   ```bash
   heroku create your-app-name
   ```

4. **Set environment variables**
   ```bash
   heroku config:set OPENAI_API_KEY=your_api_key
   heroku config:set PYTHON_VERSION=3.9.0
   ```

5. **Deploy your code**
   ```bash
   git push heroku main
   ```

### Option 3: Deploy to Azure App Service

1. **Install Azure CLI**
   ```bash
   # macOS
   brew update && brew install azure-cli
   
   # Windows
   # Download from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
   ```

2. **Login to Azure**
   ```bash
   az login
   ```

3. **Create a resource group**
   ```bash
   az group create --name mindmate-rg --location eastus
   ```

4. **Create an App Service plan**
   ```bash
   az appservice plan create --name mindmate-plan --resource-group mindmate-rg --sku F1 --is-linux
   ```

5. **Create a web app**
   ```bash
   az webapp create --resource-group mindmate-rg --plan mindmate-plan --name your-app-name --runtime "PYTHON|3.9"
   ```

6. **Set environment variables**
   ```bash
   az webapp config appsettings set --resource-group mindmate-rg --name your-app-name --settings OPENAI_API_KEY=your_api_key
   ```

7. **Deploy your code**
   - Use Azure DevOps, GitHub Actions, or FTP to deploy your code

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `PORT` | Port to run the application | No (default: 8000) |
| `PYTHON_VERSION` | Python version (e.g., 3.9.0) | Recommended |

## Post-Deployment

1. **Test your deployment**
   - Visit your app's URL in a web browser
   - Test both text and voice input
   - Check the logs for any errors

2. **Set up a custom domain (Optional)**
   - Follow your hosting provider's instructions to add a custom domain
   - Set up HTTPS for secure connections

3. **Monitoring**
   - Set up monitoring and alerts
   - Monitor API usage and costs

## Troubleshooting

- **Application not starting**: Check the logs for errors
- **Microphone not working**: Ensure the browser has microphone permissions
- **API errors**: Verify your OpenAI API key is correct and has sufficient credits

## Security Considerations

- Never commit your API keys to version control
- Use environment variables for sensitive information
- Enable HTTPS for all connections
- Implement rate limiting if necessary

## Scaling

- For production use, consider:
  - Using a production-grade ASGI server like Uvicorn with Gunicorn
  - Implementing a database for conversation history
  - Adding user authentication
  - Setting up monitoring and logging

## Support

For issues or questions, please open an issue in the repository or contact support.
