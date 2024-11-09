from locust import HttpUser, between, task

class HelloWorldUser(HttpUser):

    wait_time = between(1,3)

    @task
    def get_html(self):
        self.client.get("http://192.168.1.12:8080/index.html")

    @task
    def get_image(self):
        self.client.get("http://192.168.1.12:8080/image.png")

    @task
    def post_html(self):
        self.client.post("http://192.168.1.12:8080/index.html")

    @task
    def post_image(self):
        self.client.post("http://192.168.1.12:8080/image2.png")