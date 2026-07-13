# Streamlit Community Cloud Deployment

The application entrypoint is `app/streamlit_app.py`. It has separate modes for validated Penang 2017 aggregate completed transactions and published regional historical averages. Neither mode estimates a specific property or current 2026 value.

After the public GitHub repository is available:

1. Sign in to https://share.streamlit.io/ with GitHub.
2. Authorise access to the public repository if prompted.
3. Select `cylim0823/malaysia-house-price-estimator`.
4. Select branch `main`.
5. Set the entrypoint to `app/streamlit_app.py`.
6. Deploy.
7. Verify the aggregate-mode state/district/type/year/quarter selectors, regional mode, low-volume warnings, historical limitations, and official-source attribution.

Current deployment: https://malaysia-house-price-estimator-nnddkdymt6prvwdtkfww5y.streamlit.app

GitHub Pages cannot execute this Python application. Streamlit Community Cloud is the intended free runtime host.
