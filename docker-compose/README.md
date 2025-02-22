# Introduction

This project provides a custom implementation of the MWAA Local Runner, designed to simplify the process of running and managing MWAA containers in your local environment.
Instead of using Kubernetes, we recommend utilizing Docker Compose to build and run our containerized application.

# Why Choose Docker Compose?

While Kubernetes offers powerful features for container orchestration, it comes with a steeper learning curve and added complexity. By leveraging Docker Compose, you can enjoy
the benefits of containerization without the overhead of managing a full-fledged Kubernetes cluster in your local environment.

## Advantages over Kubernetes

### 1. Simpler Configuration

Docker Compose requires less configuration than Kubernetes, making it easier to set up and manage your MWAA Local Runner.

### 2. No Need for a Local Repository

Unlike Kubernetes, which often relies on local repositories for container images, Docker Compose can directly build and use the Docker container without the need for additional
storage or management.
