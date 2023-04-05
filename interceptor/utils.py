def build_api_url(
        plugin: str, file_name: str, mode: str = 'default',
        api_version: int = 1, trailing_slash: bool = False
):
    return f"/api/v{api_version}/{plugin}/{file_name}/{mode}{'/' if trailing_slash else ''}"
