# Use the latest official Node.js 22 on a lightweight Alpine base
FROM node:22-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker cache
COPY package*.json ./

# Install project dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port Next.js runs on
EXPOSE 3000

# The command to start the Next.js development server
CMD ["npm", "run", "dev"]