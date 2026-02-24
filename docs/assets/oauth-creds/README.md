<!--
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

- [Google Cloud OAuth Credentials Configuration](#google-cloud-oauth-credentials-configuration)
  - [Step 1: Create OAuth Credentials](#step-1-create-oauth-credentials)
  - [Step 2: Configure Authorized URIs](#step-2-configure-authorized-uris)
  - [Step 3: Save Credentials](#step-3-save-credentials)

# Google Cloud OAuth Credentials Configuration

This guide provides a step-by-step walkthrough for creating OAuth 2.0 credentials in the Google Cloud Console. These credentials are required for applications that use OAuth 2.0 to access Google APIs. For more detailed information, you can refer to the official Google Cloud documentation on [Create OAuth access credentials](https://developers.google.com/workspace/guides/create-credentials).

## Step 1: Create OAuth Credentials

Navigate to the "Credentials" page in the Google Cloud Console and click "Create Credentials". Select "OAuth client ID".

![oauth-creds Step 1 Image](/docs/assets/oauth-creds/20251105-oauth-creds-step1-get-started.png)

## Step 2: Configure Authorized URIs

Configure the authorized JavaScript origins and redirect URIs. These URIs determine where the OAuth 2.0 server can send responses. It is important to note that if you alter the UI you are using to integrate with OAuth, you will need to update these values.

*   **Authorized JavaScript origins**:
    *   `http://localhost:3000`
    *   `http://127.0.0.1:3000`
*   **Authorized redirect URIs**:
    *   `http://localhost:3000`
    *   `http://127.0.0.1:3000`
    *   `https://vertexaisearch.cloud.google.com/oauth-redirect`

The `localhost` URIs are for local development. The `vertexaisearch.cloud.google.com/oauth-redirect` URI is included for automatic support for Gemini Enterprise redirection. If the service is exposed via a load balancer, its URL should also be included here. For more information, see the [Google Cloud documentation on redirect URIs](https://developers.google.com/identity/protocols/oauth2/web-server#uri-validation).

![oauth-creds Step 2 Image](/docs/assets/oauth-creds/20251105-oauth-creds-step2-domains.png)

## Step 3: Save Credentials

After creating the credentials, you will be presented with a JSON file containing your client ID and client secret. Download and save this file in a secure location, as it will be needed for your application to use the OAuth 2.0 credentials.

![oauth-creds Step 3 Image](/docs/assets/oauth-creds/20251105-oauth-creds-step3-create-confirm.png)

You have now created a set of OAuth Credentials which can be used by consuming applications to authenticate end-users and perform Google Cloud API actions on their behalf.
