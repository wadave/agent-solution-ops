import { defineConfig, globalIgnores } from "eslint/config";
import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

import tseslint from "typescript-eslint";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default tseslint.config(
    globalIgnores([
        "**/node_modules",
        "node_modules/*",
        "./node_modules/**/*",
        "**/node_modules/**/*",
    ]),
    js.configs.recommended,
    ...tseslint.configs.recommended,
    ...compat.extends(
        "plugin:react/recommended",
        "plugin:react/jsx-runtime"
    ),
    {
        files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"],
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.commonjs,
                Atomics: "readonly",
                SharedArrayBuffer: "readonly",
            },

            ecmaVersion: "latest",
            sourceType: "module",

            parserOptions: {
                ecmaFeatures: {
                    jsx: true,
                },
            },
        },
        settings: {
            react: {
                version: "detect",
            },
        },
        rules: {},
    },
    {
        files: ["test/**/*"],
        languageOptions: {
            globals: {
                ...globals.jest,
            },
        },
    }
);
