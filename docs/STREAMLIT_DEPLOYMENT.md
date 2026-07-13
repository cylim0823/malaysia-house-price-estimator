# Streamlit Community Cloud Deployment

The application entrypoint is `app/streamlit_app.py`. Its historical mode uses one metadata-driven form for validated completed-transaction groups. Selectors come only from actual validated combinations, and quarter publication periods are handled internally. The separate individual-property mode uses the validated NAPIC completed-transaction model and rejects unsupported district/property-type segments.

After the public GitHub repository is available:

1. Sign in to https://share.streamlit.io/ with GitHub.
2. Authorise access to the public repository if prompted.
3. Select `cylim0823/malaysia-house-price-estimator`.
4. Select branch `main`.
5. Set the entrypoint to `app/streamlit_app.py`.
6. Deploy.
7. Verify both tabs, dynamic state/district/type/year selectors, the absence of a visible period selector, complete/partial/YTD labels, dataset version and age, fallback disclosure, individual-field disclosure, limitations, and official-source attribution.
8. Expand **Technical details** and confirm application build `generic-history-2026.07.13.1`.

Current deployment: https://malaysia-house-price-estimator-nnddkdymt6prvwdtkfww5y.streamlit.app

The deployment must track the branch containing the current `app/streamlit_app.py`. A legacy page with a `2017 quarter` selector or a `Show Penang district benchmark` button is not the current application.

GitHub Pages cannot execute this Python application. Streamlit Community Cloud is the intended free runtime host.
