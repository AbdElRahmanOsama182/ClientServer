from locust import HttpUser, between, task

class HelloWorldUser(HttpUser):

    wait_time = between(1,3)

    @task
    def get_html(self):
        self.client.get("/index.html")

    @task
    def get_image(self):
        self.client.get("/image.png")