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

- [Google Cloud OAuth Consent Screen Configuration](#google-cloud-oauth-consent-screen-configuration)
  - [Step 1: Navigate to OAuth Consent Screen](#step-1-navigate-to-oauth-consent-screen)
  - [Step 2: Application Information](#step-2-application-information)
  - [Step 3: Audience Configuration](#step-3-audience-configuration)
  - [Step 4: Contact Information and Completion](#step-4-contact-information-and-completion)
  - [Step 5: Authorizing Branding User Domains](#step-5-authorizing-branding-user-domains)
  - [Step 6: Add Test Users](#step-6-add-test-users)
  - [Step 7: Configure Scopes for Data Access](#step-7-configure-scopes-for-data-access)

# Google Cloud OAuth Consent Screen Configuration

This guide provides a step-by-step walkthrough for configuring the OAuth consent screen in the Google Cloud Console. This is a necessary step for applications that need to access user data. For more detailed information, you can refer to the official Google Cloud documentation on [Setting up your OAuth consent screen](https://developers.google.com/workspace/guides/configure-oauth-consent).

## Step 1: Navigate to OAuth Consent Screen

First, navigate to the OAuth Consent Screen in the Google Cloud Console. You can typically find this under "APIs & Services".

![oauth-consent Step 0 Image](/docs/assets/oauth-consent/20251105-oauth-step0-get-started.png)

## Step 2: Application Information

Fill in the application name and user support email. This information will be displayed to users when they are asked to grant consent.

![oauth-consent Step 1 Image](/docs/assets/oauth-consent/20251105-oauth-step1-app-info.png)

## Step 3: Audience Configuration

Set the "Audience" to "External". This will allow you to add test users from any email domain. For more information on user types, see the [Google Cloud documentation on user types](https://support.google.com/cloud/answer/10311615).

![oauth-consent Step 2 Image](/docs/assets/oauth-consent/20251105-oauth-step2-audience.png)

## Step 4: Contact Information and Completion

Provide a developer contact email address. This will be used by Google to notify you of any changes to your project. After this, you can save and continue to finish the initial setup.

![oauth-consent Step 3 Image](/docs/assets/oauth-consent/20251105-oauth-step3-contact-and-finish.png)

## Step 5: Authorizing Branding User Domains

If your application requires it, you can authorize specific domains for branding purposes. This step is optional.

![oauth-consent Step 4 Image](/docs/assets/oauth-consent/20251105-oauth-step4-branding-domains.png)

## Step 6: Add Test Users

After creating the consent screen, you can add test users. This is crucial for development and testing, as it allows specified users to bypass some of the verification steps.

![oauth-consent Step 5 Image](/docs/assets/oauth-consent/20251105-oauth-step5-audience-add-test-users.png)

## Step 7: Configure Scopes for Data Access

You will need to add scopes to define what user data your application can access. For this example, we are adding `userinfo.profile` and `userinfo.email`. You can find a full list of available scopes in the [OAuth 2.0 Scopes for Google APIs documentation](https://developers.google.com/identity/protocols/oauth2/scopes).

![oauth-consent Step 6 Image](/docs/assets/oauth-consent/20251105-oauth-step6-data-access-scopes.png)

Your OAuth Consent Screen has been officially configured and ready for use with this repository solution.
