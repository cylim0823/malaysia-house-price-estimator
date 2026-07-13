# Streamlit Community Cloud Deployment

The application entrypoint is `app/streamlit_app.py`. The repository includes `requirements.txt`, `.streamlit/config.toml`, and the small synthetic demonstration bundle `models/demo_bundle.pkl`; no external credentials or paid service is required.

After the public GitHub repository is available:

1. Sign in to https://share.streamlit.io/ with GitHub.
2. Authorise access to the public repository if prompted.
3. Select `cylim0823/malaysia-house-price-estimator`.
4. Select branch `main`.
5. Set the entrypoint to `app/streamlit_app.py`.
6. Deploy.
7. Verify the synthetic disclaimer and return the resulting `streamlit.app` URL.

GitHub Pages cannot execute this Python application. Streamlit Community Cloud is the intended free runtime host.

