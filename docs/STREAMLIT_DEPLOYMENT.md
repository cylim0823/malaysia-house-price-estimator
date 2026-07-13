# Streamlit Community Cloud Deployment

The application entrypoint is `app/streamlit_app.py`. Its historical mode uses one metadata-driven form for validated completed-transaction groups and published regional averages. Selectors come only from actual validated combinations. The separate individual-property mode remains disabled; neither product estimates a specific property or current 2026 value.

After the public GitHub repository is available:

1. Sign in to https://share.streamlit.io/ with GitHub.
2. Authorise access to the public repository if prompted.
3. Select `cylim0823/malaysia-house-price-estimator`.
4. Select branch `main`.
5. Set the entrypoint to `app/streamlit_app.py`.
6. Deploy.
7. Verify both dataset catalog entries, dynamic state/area/type/year/quarter selectors, low-volume warnings, historical limitations, and official-source attribution.

Current deployment: https://malaysia-house-price-estimator-nnddkdymt6prvwdtkfww5y.streamlit.app

GitHub Pages cannot execute this Python application. Streamlit Community Cloud is the intended free runtime host.
