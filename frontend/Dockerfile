FROM node:18-alpine

# Set working directory
WORKDIR /app

# Add `/app/node_modules/.bin` to $PATH
ENV PATH /app/node_modules/.bin:$PATH

# Install app dependencies
COPY package.json ./
RUN npm install --silent

# Copy app files
COPY . ./

# Build the app for production
RUN npm run build || true

# Expose port
EXPOSE 3000

# Start app
CMD ["npm", "start"]