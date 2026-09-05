# API Reference

Base URL: `http://localhost:8000`

All authenticated endpoints require the `Authorization: Bearer <token>` header.

---

## Authentication

### Register
```
POST /api/auth/register
```
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Valid email address |
| password | string | Yes | Min 8 characters |
| name | string | No | Display name |

**Response** `201 Created`:
```json
{
  "access_token": "eyJ...",
  "user": { "id": "...", "email": "...", "name": "...", "credits": 50, "plan": "FREE", "role": "user" }
}
```

### Login
```
POST /api/auth/login
```
| Field | Type | Required |
|-------|------|----------|
| email | string | Yes |
| password | string | Yes |

**Response** `200 OK`: Same as register.

### Google OAuth
```
POST /api/auth/google
```
| Field | Type | Required |
|-------|------|----------|
| credential | string | Yes | Google ID token |

### Get Current User
```
GET /api/auth/me
```
**Auth**: Required. Returns the authenticated user's profile.

### Update Profile
```
PATCH /api/auth/me
```
| Field | Type |
|-------|------|
| name | string |
| avatar_url | string |

### Change Password
```
POST /api/auth/change-password
```
| Field | Type | Required |
|-------|------|----------|
| current_password | string | Yes |
| new_password | string | Yes (min 8) |

### Forgot Password
```
POST /api/auth/forgot-password
```
| Field | Type | Required |
|-------|------|----------|
| email | string | Yes |

### Reset Password
```
POST /api/auth/reset-password
```
| Field | Type | Required |
|-------|------|----------|
| token | string | Yes |
| new_password | string | Yes |

---

## Image Generation

### Submit Generation
```
POST /api/generate
```
**Auth**: Required. Costs 1 credit.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| prompt | string | required | Text prompt |
| model | string | "stable-diffusion-xl" | AI model ID |
| width | int | 1024 | Image width |
| height | int | 1024 | Image height |
| steps | int | 30 | Sampling steps |
| cfg_scale | float | 7.5 | CFG scale |
| sampler | string | "euler_a" | Sampler name |
| seed | int | -1 | Random seed (-1 = random) |
| num_images | int | 1 | Images to generate (1-4) |
| negative_prompt | string | "" | Negative prompt |
| enhance_prompt | bool | false | Auto-enhance prompt |

**Response** `201 Created`:
```json
{
  "job_id": "uuid",
  "status": "PENDING",
  "message": "Generation queued"
}
```

### Get Job Status
```
GET /api/generate/{job_id}
```

### Stream Progress (SSE)
```
GET /api/generate/{job_id}/stream
```
Returns an `EventSource` stream with events:
```
event: progress
data: {"progress": 0.5, "status": "PROCESSING", "message": "Generating..."}

event: complete
data: {"status": "COMPLETED", "images": [...]}

event: error
data: {"status": "FAILED", "error": "..."}
```

### Cancel Generation
```
DELETE /api/generate/{job_id}
```

### List Models
```
GET /api/generate/models
```
Returns available AI models and their configurations.

### List Samplers
```
GET /api/generate/samplers
```

---

## Images

### List Images
```
GET /api/images?page=1&per_page=20&search=&model=&sort=newest
```
**Auth**: Required.

### Get Image
```
GET /api/images/{image_id}
```

### Update Image
```
PATCH /api/images/{image_id}
```
| Field | Type |
|-------|------|
| is_public | bool |
| prompt | string |

### Delete Image
```
DELETE /api/images/{image_id}
```

### Get Stats
```
GET /api/images/stats
```
Returns: `{ total_images, total_favorites, public_images, ... }`

### Toggle Favorite
```
POST /api/images/{image_id}/favorite
```
**Response**:
```json
{ "is_favorited": true, "favorites_count": 12 }
```

### Get Favorites
```
GET /api/images/user/favorites?page=1&per_page=20
```

### Create Share Link
```
POST /api/images/{image_id}/share
```
**Response**:
```json
{ "share_token": "abc123", "share_url": "http://localhost/shared/abc123" }
```

### Get Shares
```
GET /api/images/{image_id}/shares
```

### Revoke Share
```
DELETE /api/images/shares/{share_id}
```

### View Shared Image (public)
```
GET /api/images/shared/{share_token}
```
No auth required.

---

## Gallery

### List Public Images
```
GET /api/gallery?page=1&per_page=20
```
No auth required.

---

## Prompt Enhancement

### Enhance/Optimize Prompt
```
POST /api/prompts/enhance
```
**Auth**: Required.

| Field | Type | Values |
|-------|------|--------|
| prompt | string | The prompt text |
| action | string | `enhance`, `optimize`, `negative`, `suggest` |
| model_target | string | Optional target model |

**Response**:
```json
{
  "original": "a cat",
  "enhanced": "a fluffy orange cat sitting on a windowsill, soft lighting, detailed fur",
  "negative": "blurry, low quality, watermark, text",
  "tips": ["Add more specific details", "Mention lighting conditions"],
  "suggestions": null,
  "is_safe": true,
  "safety_flags": []
}
```

### Get History
```
GET /api/prompts/history?action=enhance&limit=20
```

### Get Templates
```
GET /api/prompts/templates
```

### Get Negative Templates
```
GET /api/prompts/negative-templates
```

---

## Billing

### List Plans
```
GET /api/billing/plans
```
No auth required.

### Get Plan
```
GET /api/billing/plans/{plan_id}
```

### Get Credits
```
GET /api/billing/credits
```
**Auth**: Required.

### Checkout (Stripe)
```
POST /api/billing/checkout
```
| Field | Type | Required |
|-------|------|----------|
| plan_id | string | Yes |
| success_url | string | Yes |
| cancel_url | string | Yes |

### Get Subscription
```
GET /api/billing/subscription
```

### Cancel Subscription
```
POST /api/billing/subscription/cancel
```

### List Transactions
```
GET /api/billing/transactions?page=1&per_page=20&type=deduction
```

### Get Usage Stats
```
GET /api/billing/usage
```

### Add Credits (Admin)
```
POST /api/billing/credits/add
```
| Field | Type |
|-------|------|
| amount | int |
| description | string |

### Stripe Webhook
```
POST /api/billing/webhook/stripe
```
Raw body endpoint for Stripe event processing.

---

## Admin

All admin endpoints require `role=admin`.

### Platform Stats
```
GET /api/admin/stats
```
Returns comprehensive platform metrics.

### System Health
```
GET /api/admin/health
```

### List Users
```
GET /api/admin/users?q=&role=&is_banned=&plan=&page=1&per_page=20
```

### Get User Detail
```
GET /api/admin/users/{user_id}
```

### Ban User
```
POST /api/admin/users/{user_id}/ban
```

### Unban User
```
POST /api/admin/users/{user_id}/unban
```

### Set User Role
```
PUT /api/admin/users/{user_id}/role
```
| Field | Type | Values |
|-------|------|--------|
| role | string | `user`, `admin` |

### Set User Credits
```
PUT /api/admin/users/{user_id}/credits
```

### List Images (Admin)
```
GET /api/admin/images?q=&user_id=&model=&is_public=&page=1
```

### Prompt Analytics
```
GET /api/admin/prompts/analytics?days=30
```

### Audit Logs
```
GET /api/admin/audit-logs?admin_id=&action=&target_type=&page=1
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request |
| 401 | Unauthenticated (invalid/missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate email) |
| 422 | Validation error (invalid request body) |
| 429 | Rate limited |
| 500 | Internal server error |
