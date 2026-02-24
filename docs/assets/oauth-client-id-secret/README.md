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

- [Storing OAuth Credentials in Google Cloud Secret Manager](#storing-oauth-credentials-in-google-cloud-secret-manager)
  - [Step 1: Create a Secret](#step-1-create-a-secret)
  - [Step 2: Add Secret Value](#step-2-add-secret-value)
  - [Step 2: Repeat Stepsd 1-2 for OAuth Client Secret](#step-2-repeat-stepsd-1-2-for-oauth-client-secret)

# Storing OAuth Credentials in Google Cloud Secret Manager

This guide provides a step-by-step walkthrough for securely storing your OAuth 2.0 client ID and client secret in Google Cloud Secret Manager. Secret Manager is a secure and convenient storage system for API keys, passwords, certificates, and other sensitive data. For more detailed information, you can refer to the official Google Cloud documentation on [Secret Manager](https://cloud.google.com/secret-manager/docs).

## Step 1: Create a Secret

Navigate to the Secret Manager page in the Google Cloud Console and click "Create Secret".

![oauth-client-id-secret Step 1 image](/docs/assets/oauth-client-id-secret/20251105-oauth-id-secret-step1-click-create-secret.png)

## Step 2: Add Secret Value

Provide a name for your secret and add the OAuth client ID as the secret value. It is recommended to store the client ID and client secret as separate secrets. For more information on creating and managing secrets, see the [Google Cloud documentation on creating secrets](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets).

![oauth-client-id-secret Step 2 image](/docs/assets/oauth-client-id-secret/20251105-oauth-id-secret-step2-create-secret-values.png)

## Step 2: Repeat Stepsd 1-2 for OAuth Client Secret

If required, repeat steps #1 and #2 for the OAuth Client Secret, stored in OAUTH_CLIENT_SECRET.


Your downstream applications are now ready to access your OAuth client ID via secret "OAUTH_CLIENT_ID".
