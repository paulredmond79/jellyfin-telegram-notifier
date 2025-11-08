"""Tests for Swagger UI documentation endpoint."""


class TestSwaggerUI:
    """Test Swagger UI endpoints."""

    def test_docs_endpoint_exists(self, client):
        """Test that /docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_docs_endpoint_returns_html(self, client):
        """Test that /docs returns HTML content."""
        response = client.get("/docs")
        assert response.content_type.startswith("text/html")
        assert b"swagger-ui" in response.data.lower() or b"swagger" in response.data.lower()

    def test_apispec_endpoint_exists(self, client):
        """Test that /apispec.json endpoint is accessible."""
        response = client.get("/apispec.json")
        assert response.status_code == 200

    def test_apispec_returns_json(self, client):
        """Test that /apispec.json returns JSON."""
        response = client.get("/apispec.json")
        assert response.content_type == "application/json"

    def test_apispec_contains_swagger_info(self, client):
        """Test that apispec contains proper Swagger information."""
        response = client.get("/apispec.json")
        data = response.get_json()

        assert "swagger" in data
        assert "info" in data
        assert data["info"]["title"] == "Jellyfin Telegram Notifier API"
        assert "version" in data["info"]

    def test_apispec_contains_webhook_endpoint(self, client):
        """Test that apispec documents the webhook endpoint."""
        response = client.get("/apispec.json")
        data = response.get_json()

        assert "paths" in data
        assert "/webhook" in data["paths"]
        assert "post" in data["paths"]["/webhook"]

    def test_webhook_endpoint_has_documentation(self, client):
        """Test that webhook endpoint has proper OpenAPI documentation."""
        response = client.get("/apispec.json")
        data = response.get_json()

        webhook_spec = data["paths"]["/webhook"]["post"]

        # Check basic documentation fields
        assert "summary" in webhook_spec
        assert "description" in webhook_spec
        assert "parameters" in webhook_spec
        assert "responses" in webhook_spec

    def test_webhook_endpoint_has_tags(self, client):
        """Test that webhook endpoint is properly tagged."""
        response = client.get("/apispec.json")
        data = response.get_json()

        webhook_spec = data["paths"]["/webhook"]["post"]
        assert "tags" in webhook_spec
        assert "webhook" in webhook_spec["tags"]

    def test_apispec_defines_tags(self, client):
        """Test that apispec defines the tags used."""
        response = client.get("/apispec.json")
        data = response.get_json()

        assert "tags" in data
        tag_names = [tag["name"] for tag in data["tags"]]
        assert "webhook" in tag_names
