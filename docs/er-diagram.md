# Database ER Diagram

## Entity Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        varchar email UK
        varchar name
        varchar avatar_url
        varchar hashed_password
        varchar oauth_provider
        varchar oauth_id
        int credits
        varchar plan
        varchar role
        boolean is_active
        boolean is_banned
        text ban_reason
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }

    PLANS {
        uuid id PK
        varchar name UK
        varchar display_name
        text description
        int monthly_credits
        decimal monthly_price
        int max_concurrent_jobs
        boolean is_active
        int sort_order
        timestamptz created_at
    }

    IMAGES {
        uuid id PK
        uuid user_id FK
        text prompt
        text enhanced_prompt
        text negative_prompt
        varchar model
        int width
        int height
        varchar image_url
        varchar thumbnail_url
        int seed
        int steps
        float cfg_scale
        varchar sampler
        varchar status
        boolean is_public
        int likes_count
        jsonb metadata
        timestamptz created_at
    }

    JOBS {
        uuid id PK
        uuid user_id FK
        varchar status
        varchar provider
        varchar model
        jsonb parameters
        jsonb result
        text error_message
        float progress
        timestamptz started_at
        timestamptz completed_at
        timestamptz created_at
    }

    IMAGE_TAGS {
        uuid id PK
        uuid image_id FK
        varchar tag
    }

    USER_LIKES {
        uuid id PK
        uuid user_id FK
        uuid image_id FK
        timestamptz created_at
    }

    PASSWORD_RESET_TOKENS {
        uuid id PK
        uuid user_id FK
        varchar token_hash UK
        timestamptz expires_at
        boolean used
        timestamptz created_at
    }

    PROMPT_HISTORY {
        uuid id PK
        uuid user_id FK
        text original_prompt
        text enhanced_prompt
        text negative_prompt
        varchar action
        varchar model_target
        jsonb metadata
        boolean is_safe
        jsonb safety_flags
        timestamptz created_at
    }

    IMAGE_FAVORITES {
        uuid id PK
        uuid user_id FK
        uuid image_id FK
        timestamptz created_at
    }

    IMAGE_SHARES {
        uuid id PK
        uuid user_id FK
        uuid image_id FK
        varchar share_token UK
        varchar share_url
        int view_count
        boolean is_active
        timestamptz expires_at
        timestamptz created_at
    }

    SUBSCRIPTIONS {
        uuid id PK
        uuid user_id FK
        varchar stripe_subscription_id
        varchar stripe_customer_id
        varchar status
        timestamptz current_period_start
        timestamptz current_period_end
        timestamptz created_at
        timestamptz updated_at
    }

    CREDIT_TRANSACTIONS {
        uuid id PK
        uuid user_id FK
        varchar type
        int amount
        int balance_after
        varchar description
        varchar reference_type
        varchar reference_id
        timestamptz created_at
    }

    USAGE_LOGS {
        uuid id PK
        uuid user_id FK
        varchar action
        int credits_used
        varchar model
        jsonb metadata
        timestamptz created_at
    }

    ADMIN_AUDIT_LOGS {
        uuid id PK
        uuid admin_id FK
        varchar action
        varchar target_type
        varchar target_id
        jsonb details
        timestamptz created_at
    }

    USERS ||--o{ IMAGES : "creates"
    USERS ||--o{ JOBS : "submits"
    USERS ||--o{ USER_LIKES : "likes"
    USERS ||--o{ PASSWORD_RESET_TOKENS : "requests"
    USERS ||--o{ PROMPT_HISTORY : "enhances"
    USERS ||--o{ IMAGE_FAVORITES : "favorites"
    USERS ||--o{ IMAGE_SHARES : "shares"
    USERS ||--o{ SUBSCRIPTIONS : "subscribes"
    USERS ||--o{ CREDIT_TRANSACTIONS : "earns/spends"
    USERS ||--o{ USAGE_LOGS : "uses"
    USERS ||--o{ ADMIN_AUDIT_LOGS : "administers"

    IMAGES ||--o{ IMAGE_TAGS : "tagged with"
    IMAGES ||--o{ USER_LIKES : "liked by"
    IMAGES ||--o{ IMAGE_FAVORITES : "favorited by"
    IMAGES ||--o{ IMAGE_SHARES : "shared via"
```

## Table Descriptions

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | User accounts with auth, credits, role | email (unique), hashed_password, credits, role, is_banned |
| `plans` | Subscription plan definitions | name (unique), monthly_credits, monthly_price |
| `images` | Generated image metadata | prompt, model, image_url, is_public, likes_count |
| `jobs` | Image generation job queue | status (PENDING/PROCESSING/COMPLETED/FAILED), progress |

### Auth Tables

| Table | Purpose |
|-------|---------|
| `password_reset_tokens` | Hashed tokens for password reset flow (30min expiry) |

### Social Tables

| Table | Purpose |
|-------|---------|
| `user_likes` | Many-to-many: users ↔ images (public gallery) |
| `image_favorites` | Many-to-many: users ↔ images (private collection) |
| `image_shares` | Shareable links with view counts and expiry |
| `image_tags` | Flexible tagging system for images |

### AI Tables

| Table | Purpose |
|-------|---------|
| `prompt_history` | Log of all prompt enhancements with safety analysis |

### Billing Tables

| Table | Purpose |
|-------|---------|
| `subscriptions` | Stripe subscription tracking |
| `credit_transactions` | Full ledger of credit additions and deductions |
| `usage_logs` | Granular usage analytics (model, action, credits) |

### Admin Tables

| Table | Purpose |
|-------|---------|
| `admin_audit_logs` | Complete audit trail of all admin actions |

## Migration History

| Version | Name | Changes |
|---------|------|---------|
| 001 | initial | users, plans, images, jobs, image_tags, user_likes |
| 002 | auth | password_reset_tokens |
| 003 | prompt_history | prompt_history |
| 004 | favorites_shares | image_favorites, image_shares |
| 005 | billing | subscriptions, credit_transactions, usage_logs |
| 006 | admin | role, is_banned columns on users; admin_audit_logs |
