FROM node:18

# Set working directory
WORKDIR /app

# Add `/app/node_modules/.bin` to $PATH
ENV PATH /app/node_modules/.bin:$PATH

# Install app dependencies
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy app files
COPY . ./

# Build the app for production
RUN npm run build || true

# Expose port
EXPOSE 3000

# Start app
CMD ["npm", "start"]