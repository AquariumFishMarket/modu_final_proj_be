# API 상세

## Auth (회원가입 / 로그인 / 로그아웃 / 탈퇴 / 토큰 갱신)

### 1. POST `/api/auth/signup`

- **설명** : 새로운 사용자 계정 생성 (회원가입)

#### Request

- **Headers**
    - `Content-type`: application/json

- **Body** : SignupRequest
    - raw
    ```json
    {
        "email": "testuser@example.com",
        "password": "securepassword"
    }
    ```

#### Response
- SignupResponse (정상 응답 시)
```json
{
    "user_id": 1,
    "email": "testuser@example.com",
    "created_at": "2025-11-13T10:04:35.880059+09:00"
}
```

#### 비고
- 정상 응답 시 DB users 테이블에 해당 사용자 관련 row가 추가됨
- 이미 존재하는 사용자의 email과 동일한 email로 request를 전송할 경우 HTTPException 발생


### 2. POST `/api/auth/login`

- **설명** : 이메일과 비밀번호를 통해 로그인
    - 첫 로그인 여부(해당 사용자의 account_id 존재 여부)에 따라 응답 구조가 달라짐

#### Request

- **Headers**
    - `Content-type`: application/json

- **Body** : LoginRequest
    - raw
    ```json
    {
        "email": "testuser@example.com",
        "password": "securepassword"
    }
    ```

#### Response
- LoginResponse (정상 응답. 첫 로그인 시)
```json
{
    "access_token": null,
    "refresh_token": null,
    "temporary_token": "<temp_token>",
    "token_type": "bearer",
    "is_initial_login": true,
    "user_id": 1,
    "account_id": null,
    "username": null
}
```

- LoginResponse (정상 응답. 기존 사용자의 로그인일 경우)
```json
{
    "access_token": "<access_token>",
    "refresh_token": "<refresh_token>",
    "temporary_token": null,
    "token_type": "bearer",
    "is_initial_login": false,
    "user_id": 1,
    "account_id": "test123",
    "username": "testuser"
}
```

#### 비고
- 첫 로그인 시, DB의 sessions 테이블에 해당 사용자를 위한 세션 row가 할당되지 않음. temporary_token만 발급받고, 이를 LoginResponse에서 확인 가능
- 일반 로그인인 경우, access_token과 refresh_token을 발급받고, 이를 LoginResponse에서 확인 가능. refresh_token은 `/api/auth/refresh`나 `api/auth/logout`에서 사용됨
- email과 password를 올바르게 입력하지 않거나, 비활성화된 사용자 계정일 경우 HTTPException 발생

### 3. POST `/api/auth/logout`

- **설명** : refresh_token을 검증하여, DB 내 세션을 무효화하여 로그아웃 처리

#### Request

- **Headers**
    - `Content-type`: application/json

- **Body** : LogoutRequest
    - raw
    ```json
    {
        "refresh_token": "<refresh_token>"
    }
    ```

#### Response
- 정상 응답 시
```json
{
    "detail": "로그아웃이 완료되었습니다."
}
```

#### 비고
- 전달된 refresh_token이 유효하지 않거나 만료된 경우 HTTPException 발생


### 4. DELETE `/api/auth/withdraw`

- **설명**: Access Token 기반 회원 탈퇴.
    - 비밀번호 확인 후 Soft Delete (is_active=False 처리). 해당 사용자의 계정 비활성화시킴.
    - 해당 사용자의 모든 세션 무효화

#### Request

- **Headers**
    - `Content-type`: application/json
    - `Authorization`: bearer `<access_token>`

- **Body** : WithdrawRequest
    - raw
    ```json
    {
        "password": "securepassword"
    }
    ```

#### Response
- 정상 응답 시
```json
{
    "detail": "회원 탈퇴가 완료되었습니다."
}
```

#### 비고
- 현재 로그인된 사용자의 올바른 password를 request로 전송하지 않으면 HTTPException 발생


### 5. POST `/api/auth/refresh`

- **설명** : refresh_token 기반 access_token 재발급

#### Request

- **Headers**
    - `Content-type`: application/json

- **Body** : RefreshRequest
    - raw
    ```json
    {
        "refresh_token": "<refresh_token>"
    }
    ```

#### Response
- TokenPayload (정상 응답 시)
```json
{
    "access_token": "<new_access_token>",
    "refresh_token": "<refresh_token>",
    "token_type": "bearer"
}
```

#### 비고
- 정상 응답 시, 새 access_token을 발급받고, refresh_token은 기존의 것을 유지. DB sessions 테이블에는 새 access_token에 대한 row가 추가됨.
- 기간이 만료되었거나, 현재 로그인한 사용자의 refresh_token과 일치하지 않은 refresh_token을 request로 전송할 경우 HTTPException 발생

## User

### 1. POST `/api/users/initial-profile`

- **설명** : 회원가입 후 첫 로그인 시 프로필 정보 설정

#### Request

- **Headers**
    - `Content-type`: multipart/form-data
    - `Authorization`: bearer `<temp_token>`

- **Body** : InitialProfileRequest

    - form-data

    | key | type | example |
    |------|------|----------|
    | username | text | `testuser` |
    | account_id | text | `test123` |
    | bio | text | `안녕하세요.` |
    | profile_image | file | `profile.jpg` |

    - username, account_id는 필수 입력

#### Response
- InitialProfileResponse (정상 응답 시)
```json
{
    "id": 1,
    "account_id": "test123",
    "username": "testuser",
    "email": "testuser@example.com",
    "bio": "안녕하세요",
    "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/1cfc5514-2bf2-4183-9534-28e50a23569d.jpg",
    "is_active": true,
    "access_token": "<access_token>",
    "refresh_token": "<refresh_token>",
    "token_type": "bearer"
}
```

#### 비고
- 정상 응답 시, DB users 테이블에서 해당 사용자의 row에 사용자 정보가 업데이트됨. S3 버킷에는 해당 사용자의 프로필 이미지가 저장됨.
- 이미 존재하는 사용자의 account_id와 동일한 account_id로 request를 전송할 경우 HTTPException 발생
- request body에 username, account_id에 대한 정보를 입력하지 않고 request를 전송할 경우 HTTPException 발생


### 2. GET `/api/users/me`

- **설명** : 로그인한 사용자 자신의 프로필 조회

#### Request

- **Headers**
    - `Content-type` : application/json
    - `Authorization` : bearer `<access_token>`

#### Response
- UserDetailResponse (정상 응답 시)
```json
{
    "id": 1,
    "account_id": "test123",
    "username": "testuser",
    "email": "testuser@example.com",
    "bio": "안녕하세요",
    "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "is_active": true,
    "created_at": "2025-11-13T17:12:20.958165+09:00",
    "updated_at": "2025-11-13T17:13:30.514318+09:00",
    "follower_count": 1,
    "following_count": 0
}
```

#### 비고
- access_token이 만료되었거나 잘못된 경우 HTTPException 발생


### 3. PATCH `/api/users/me`

- **설명** : 자신의 프로필 정보 수정

#### Request

- **Headers**
    - `Content-Type` : multipart/form-data
    - `Authorization` : bearer `<access_token>`

- **Body** : UserUpdateRequest
    - form-data

    | key | type | example |
    |------|------|----------|
    | username | text | `testuser1` |
    | account_id | text | `test124` |
    | bio | text | `변경된 자기소개` |
    | profile_image | file | `new_profile.jpg` |

    - 모든 필드는 **optional**

#### Response
- UserDetailResponse (정상 응답 시)
```json
{
    "id": 1,
    "account_id": "test124",
    "username": "testuser1",
    "email": "testuser@example.com",
    "bio": "변경된 자기소개",
    "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "is_active": true,
    "created_at": "2025-11-13T17:12:20.958165+09:00",
    "updated_at": "2025-11-13T17:51:11.652801+09:00",
    "follower_count": 1,
    "following_count": 0
}
```

#### 비고
- 이미 존재하는 account_id를 request로 전송 시 HTTPException 발생


### 4. GET `/api/users/search`
- **설명** : username 기준으로, 사용자 검색. 부분적으로 일치해도 검색됨.

#### Request

- **Query Parameters**

| key | example |
| --- | ------- |
| name | test |

-> url 구조는 `/api/users/search?name=test`가 됨.

#### Response
- UserListItem[] (정상 응답 시)
```json
[
    {
        "id": 1,
        "account_id": "test123",
        "username": "testuser",
        "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg"
    },
    {
        "id": 8,
        "account_id": "test234",
        "username": "testuser2",
        "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/cc35be85-6cc1-4f4c-bc40-ffc1946c6b6e.jpg"
    }
]
```

#### 비고
- 검색 결과가 없으면 빈 배열 `[]` 반환
- 대소문자 구분없이 검색


### 5. GET `/api/users/{user_id}`
- **설명** : 특정 사용자의 프로필 정보 조회

#### Request
- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 1 |

-> url 구조는 `/api/users/1`이 됨.

#### Response
- UserDetailResponse (정상 응답 시)
```json
{
    "id": 1,
    "account_id": "test123",
    "username": "testuser",
    "email": "testuser@example.com",
    "bio": "안녕하세요",
    "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "is_active": true,
    "created_at": "2025-11-13T17:12:20.958165+09:00",
    "updated_at": "2025-11-13T17:51:11.652801+09:00",
    "follower_count": 1,
    "following_count": 0
}
```

#### 비고
- 존재하지 않는 사용자일 경우 HTTPException 발생


### 6. Post `/api/users/{user_id}/follow`
- **설명** : 로그인 중인 사용자가 특정 사용자를 팔로우

#### Request

- **Headers**
    - `Content-Type` : application/json
    - `Authorizaton` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 1 |

-> url 구조는 `/api/users/1/follow`가 됨.

#### Response
- 정상 응답 시
```json
{
    "detail": "사용자를 팔로우했습니다."
}
```

#### 비고
- 이미 팔로우 중인 경우 HTTPException 발생
- 자기 자신을 팔로우 시도할 경우 HTTPException 발생


### 7. DELETE `/api/users/{user_id}/follow`
- **설명** : 로그인 중인 사용자가 특정 사용자를 언팔로우

#### Request

- **Headers**
    - `Content-Type` : application/json
    - `Authorizaton` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 1 |

-> url 구조는 `/api/users/1/follow`가 됨.

#### Response
- 정상 응답 시
```json
{
    "detail": "사용자 언팔로우 완료."
}
```

#### 비고
- 팔로우 중이 아닐 경우 HTTPException 발생


### 8. GET `/api/users/{user_id}/followers`
- **설명** : 특정 사용자의 팔로워 목록 조회

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 1 |

-> url 구조는 `/api/users/1/followers`가 됨.

#### Response

- FollowResponse[] (정상 응답 시)
```json
[
    {
        "id": 8,
        "account_id": "test234",
        "username": "testuser2",
        "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/cc35be85-6cc1-4f4c-bc40-ffc1946c6b6e.jpg"
    }
]
```

#### 비고
- 해당 사용자의 팔로워가 없으면 빈 배열 `[]` 반환


### 9. GET `/api/users/{user_id}/followings`
- **설명** : 특정 사용자의 팔로잉 목록 조회

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 8 |

-> url 구조는 `/api/users/8/followings`가 됨.

#### Response
- FollowResponse[] (정상 응답 시)
```json
[
    {
        "id": 1,
        "account_id": "test123",
        "username": "testuser",
        "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg"
    }
]
```

#### 비고
- 해당 사용자의 팔로워가 없으면 빈 배열 `[]` 반환


### 10. GET `/api/users/{user_id}/products`
- **설명**: 특정 사용자가 등록한 상품 목록 조회

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 6 |

-> url 구조는 `/api/users/6/products`가 됨.

#### Response

- ProductDetailResponse[] (정상 응답 시)
```json
[
    {
        "id": 2,
        "name": "다이어그램들",
        "description": "새로 추가한 다이어그램이 있습니다.",
        "price": 20000.0,
        "product_url": "http://another-fake-product/erd",
        "image_urls": [
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/f3c1422a-7f7e-4cd1-9334-5674e396c667.png",
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/c6e81efb-8d33-4e41-b32c-2ef11a1b5405.png",
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/3f9a3701-0519-4350-ac75-0f0188bf234a.png"
        ],
        "seller_id": 6,
        "seller_account_id": "test123",
        "seller_username": "testuser",
        "seller_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "like_count": 1,
        "view_count": 1,
        "created_at": "2025-11-14T16:52:27.918732+09:00",
        "updated_at": "2025-11-14T17:15:38.464857+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0
    }
]
```

#### 비고
- 사용자가 존재하지 않을 경우 HTTPException 발생
- 해당 사용자가 등록한 상품이 없을 경우 빈 배열 `[]` 반환

### 11. GET `/api/users/{user_id}/likes/products`
- **설명** : 특정 사용자가 좋아요한 상품 목록 조회

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 6 |

-> url 구조는 `/api/users/6/likes/products`가 됨.

#### Response

- ProductDetailResponse[] (정상 응답 시)
```json
[
    {
        "id": 2,
        "name": "변경된 다이어그램들",
        "description": "새로 추가한 다이어그램이 있습니다.",
        "price": 20000.0,
        "product_url": "http://another-fake-product/erd",
        "image_urls": [
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/f3c1422a-7f7e-4cd1-9334-5674e396c667.png",
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/c6e81efb-8d33-4e41-b32c-2ef11a1b5405.png",
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/3f9a3701-0519-4350-ac75-0f0188bf234a.png"
        ],
        "seller_id": 6,
        "seller_account_id": "test123",
        "seller_username": "testuser",
        "seller_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "like_count": 1,
        "view_count": 1,
        "created_at": "2025-11-14T16:52:27.918732+09:00",
        "updated_at": "2025-11-14T17:15:38.464857+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0
    }
]
```

#### 비고
- 사용자가 존재하지 않을 경우 HTTPException 발생
- 좋아요한 상품이 없으면 빈 배열 `[]` 반환

### 12. GET `/api/users/{user_id}/posts`
- **설명** : 특정 사용자가 작성한 게시글 목록 조회

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 6 |

-> url 구조는 `/api/users/6/posts`가 됨.

#### Response

- PostDetailResponse[] (정상 응답 시)
```json
[
    {
        "id": 3,
        "title": "첫 게시글입니다.",
        "content": "이것은 첫 게시글",
        "image_urls": [
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/3417c0af-9d12-431e-9d5d-9bc71a088192.png",
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/bcd02cb4-3adf-41d9-a0d1-e90f11cb288b.png"
        ],
        "author_id": 6,
        "author_account_id": "test123",
        "author_username": "testuser",
        "author_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "hashtags": [
            {
                "id": 1,
                "name": "열대어"
            },
            {
                "id": 3,
                "name": "테라리움"
            }
        ],
        "like_count": 0,
        "comment_count": 0,
        "view_count": 0,
        "created_at": "2025-11-17T14:20:53.570229+09:00",
        "updated_at": "2025-11-17T14:20:53.570229+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0
    },
    {
        "id": 2,
        "title": "첫 게시글입니다.",
        "content": "이것은 첫 게시글",
        "image_urls": [
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/9a1ee3a7-4a80-42d8-b740-f7e7c7ef0b14.png",
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/14ed90d3-ff3c-491f-9efb-2a1b15f69d7f.png"
        ],
        "author_id": 6,
        "author_account_id": "test123",
        "author_username": "testuser",
        "author_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "hashtags": [
            {
                "id": 1,
                "name": "열대어"
            },
            {
                "id": 2,
                "name": "소형"
            }
        ],
        "like_count": 0,
        "comment_count": 0,
        "view_count": 1,
        "created_at": "2025-11-17T14:20:18.334643+09:00",
        "updated_at": "2025-11-17T14:21:30.012338+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0
    }
]
```

#### 비고
- 사용자가 존재하지 않을 경우 HTTPException 발생
- 해당 사용자가 작성한 게시글이 없을 경우 빈 배열 `[]` 반환


### 13. GET `/api/users/{user_id}/likes/posts`
- **설명** : 특정 사용자가 좋아요한 게시글 목록 조회

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| user_id | 6 |

-> url 구조는 `/api/users/6/likes/posts`가 됨.

#### Response

- PostDetailResponse[] (정상 응답 시)
```json
[
    {
        "id": 2,
        "title": "제목이 수정된 게시글",
        "content": "이 게시글은 수정되었습니다",
        "image_urls": [
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/7178fc98-bb48-4152-af4c-ff9e353cb8e4.png",
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/7a5885dd-9021-4ddd-9cd0-53fda46a323e.png"
        ],
        "author_id": 6,
        "author_account_id": "test123",
        "author_username": "testuser",
        "author_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "hashtags": [
            {
                "id": 4,
                "name": "수정된 태그"
            },
            {
                "id": 5,
                "name": "새로 추가된 태그"
            }
        ],
        "like_count": 1,
        "comment_count": 0,
        "view_count": 1,
        "created_at": "2025-11-17T14:20:18.334643+09:00",
        "updated_at": "2025-11-17T14:24:02.670078+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0
    }
]
```

#### 비고
- 사용자가 존재하지 않을 경우 HTTPException 발생
- 좋아요한 게시글이 없으면 빈 배열 `[]` 반환

## Product

### 1. POST `/api/product`
- **설명** : 새로운 상품 등록
    - 이미지 파일 여러 장 (최대 5장) 업로드 가능

#### Request

- **Headers**
    - `Content-Type` : multipart/form-data
    - `Authorization` : bearer `<access_token>`

- **Body** : ProductCreate

    - form-data

    | key | type | example |
    |------|------|----------|
    | name | text | `새 다이어그램` |
    | description | text | `간단한 다이어그램들입니다` |
    | price | text | `10000` |
    | product_url | text | `http://fake-product/erd` |
    | images  | file | |

    - name, price는 필수 입력

#### Response

- ProductDetailResponse (정상 응답 시)
```json
{
    "id": 5,
    "name": "새 다이어그램들",
    "description": "간단한 다이어그램들입니다.",
    "price": 10000.0,
    "product_url": "http://fake-product/erd",
    "image_urls": [],
    "seller_id": 6,
    "seller_account_id": "test123",
    "seller_username": "testuser",
    "seller_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "like_count": 0,
    "view_count": 0,
    "created_at": "2025-11-14T17:15:15.908922+09:00",
    "updated_at": "2025-11-14T17:15:15.908922+09:00",
    "is_blurred": false,
    "is_deleted": false,
    "report_count": 0
}
```

#### 비고
- 이미지 파일이 있을 경우 S3 스토리지에 업로드됨.
- 이미지 파일을 5개보다 많이 첨부해서 request 전송할 경우 HTTPException 발생


### 2. GET `/api/products/{product_id}`
- **설명** : 특정 상품 상세 조회

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| product_id | 2 |

-> url 구조는 `/api/products/2`가 됨.

#### Response

- ProductDetailResponse (정상 응답 시)
```json
{
    "id": 2,
    "name": "다이어그램들",
    "description": "다이어그램",
    "price": 12000.0,
    "product_url": "http://fake-product/erd",
    "image_urls": [],
    "seller_id": 6,
    "seller_account_id": "test123",
    "seller_username": "testuser",
    "seller_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "like_count": 0,
    "view_count": 1,
    "created_at": "2025-11-14T16:52:27.918732+09:00",
    "updated_at": "2025-11-14T17:08:52.549388+09:00",
    "is_blurred": false,
    "is_deleted": false,
    "report_count": 0
}
```

#### 비고
- 해당 api 조회 시, view_count(조회수) 1 증가
- 존재하지 않은 상품 조회 시 HTTPException 발생


### 3. PUT `/api/products/{product_id}`
- **설명** : 사용자 자신의 상품 수정
    - 이미지 파일 여러 장 (최대 5장) 업로드 가능

#### Request

- **Headers**
    - `Content-Type` : multipart/form-data
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| product_id | 2 |

-> url 구조는 `/api/products/2`가 됨.

- **Body** : ProductUpdate

    - form-data

    | key | type | example |
    |------|------|----------|
    | name | text | `변경된 다이어그램들` |
    | description | text | `새로 추가한 다이어그램이 있습니다.` |
    | price | text | `20000` |
    | product_url | text | `http://another-fake-product/erd` |
    | images  | file | [ `product01.jpg`, `product02.jpg`, `product03.jpg`] |

    - 모든 필드는 **optional**

#### Response

- ProductDetailResponse (정상 응답 시)
```json
{
    "id": 2,
    "name": "변경된 다이어그램들",
    "description": "새로 추가한 다이어그램이 있습니다.",
    "price": 20000.0,
    "product_url": "http://another-fake-product/erd",
    "image_urls": [
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/f3c1422a-7f7e-4cd1-9334-5674e396c667.png",
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/c6e81efb-8d33-4e41-b32c-2ef11a1b5405.png",
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/products/3f9a3701-0519-4350-ac75-0f0188bf234a.png"
    ],
    "seller_id": 6,
    "seller_account_id": "test123",
    "seller_username": "testuser",
    "seller_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "like_count": 0,
    "view_count": 1,
    "created_at": "2025-11-14T16:52:27.918732+09:00",
    "updated_at": "2025-11-14T17:08:52.549388+09:00",
    "is_blurred": false,
    "is_deleted": false,
    "report_count": 0
}
```

#### 비고
- 제공된 필드만 업데이트됨.
- 사용자 본인이 등록하지 않은 상품을 수정하려고 하면 HTTPException 발생


### 4. DELETE `/api/products/{product_id}`
- **설명** : 자신의 상품을 삭제

#### Request

- **Headers**
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| product_id | 4 |

-> url 구조는 `/api/products/4`가 됨.

#### Response

- 정상 응답 시
```json
{
    "detail": "상품이 삭제되었습니다."
}
```

#### 비고
- 본인이 등록하지 않은 상품을 삭제 시도 시 HTTPException 발생
- 실제 상품 삭제가 아닌, Soft Delete 방식(is_deleted=True 처리)

### 5. POST `/api/products/{product_id}/likes`
- **설명** : 특정 상품 좋아요 등록

#### Request

- **Headers**
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| product_id | 2 |

-> url 구조는 `/api/products/2/likes`가 됨.

#### Response

- 정상 응답 시
```json
{
    "detail": "좋아요가 등록되었습니다."
}
```

#### 비고
- 이미 좋아요한 상품에 대해 좋아요 등록 시도 시 HTTPException 발생
- 본인이 등록한 상품에 대해 좋아요 등록도 가능


### 6. DELETE `/api/products/{product_id}/likes`
- **설명** : 특정 상품 좋아요 취소

#### Request

- **Headers**
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| product_id | 2 |

-> url 구조는 `/api/products/2/likes`가 됨.

#### Response

- 정상 응답 시
```json
{
    "detail": "좋아요가 취소되었습니다."
}
```

#### 비고
- 좋아요 등록하지 않은 상품을 좋아요 취소 시도할 경우 HTTPException 발생


## Post

### 1. GET `/api/posts/feed`
- **설명** : 로그인한 사용자가 팔로우한 유저들의 게시글 조회

#### Request

- **Headers**
    - `Authorization` : bearer `<access_token>`

#### Response

- PostDetailResponse[] (정상 응답 시)
```json
[
    {
        "id": 2,
        "title": "제목이 수정된 게시글",
        "content": "이 게시글은 수정되었습니다",
        "image_urls": [
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/7178fc98-bb48-4152-af4c-ff9e353cb8e4.png",
            "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/7a5885dd-9021-4ddd-9cd0-53fda46a323e.png"
        ],
        "author_id": 6,
        "author_account_id": "test123",
        "author_username": "testuser",
        "author_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "hashtags": [
            {
                "id": 4,
                "name": "수정된 태그"
            },
            {
                "id": 5,
                "name": "새로 추가된 태그"
            }
        ],
        "like_count": 1,
        "comment_count": 0,
        "view_count": 1,
        "created_at": "2025-11-17T14:20:18.334643+09:00",
        "updated_at": "2025-11-17T14:25:05.442793+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0
    }
]
```

#### 비고
- 팔로우한 사용자가 없다면 빈 배열 `[]` 반환


### 2. POST `/api/posts`
- **설명** : 새 게시글 작성
    - 이미지 최대 10장 업로드 가능

#### Request

- **Headers**
    - `Content-Type` : multipart/form-data
    - `Authorization` : bearer `<access_token>`

- **Body** : PostCreate

    - form-data

    | key | type | example |
    |------|------|----------|
    | title | text | `첫 게시글입니다.` |
    | content | text | `이것은 첫 게시글` |
    | images  | file | [`image1.png`, `image2.png`] |
    | hashtags | text | [`열대어`, `테라리움`] |

    - title, content는 필수 입력

#### Response

- PostDetailResponse (정상 응답 시)
```json
{
    "id": 3,
    "title": "첫 게시글입니다.",
    "content": "이것은 첫 게시글",
    "image_urls": [
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/3417c0af-9d12-431e-9d5d-9bc71a088192.png",
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/bcd02cb4-3adf-41d9-a0d1-e90f11cb288b.png"
    ],
    "author_id": 6,
    "author_account_id": "test123",
    "author_username": "testuser",
    "author_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "hashtags": [
        {
            "id": 1,
            "name": "열대어"
        },
        {
            "id": 3,
            "name": "테라리움"
        }
    ],
    "like_count": 0,
    "comment_count": 0,
    "view_count": 0,
    "created_at": "2025-11-17T14:20:53.570229+09:00",
    "updated_at": "2025-11-17T14:20:53.570229+09:00",
    "is_blurred": false,
    "is_deleted": false,
    "report_count": 0
}
```

#### 비고
- 이미지 파일이 있을 경우 S3 스토리지에 업로드됨.


### 3. GET `/api/posts/{post_id}`
- **설명** : 게시글 상세 조회. 조회수 1 증가


#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |

-> url 구조는 `/api/posts/2`가 됨.

#### Response

- PostDetailResponse (정상 응답 시)
```json
{
    "id": 2,
    "title": "첫 게시글입니다.",
    "content": "이것은 첫 게시글",
    "image_urls": [
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/9a1ee3a7-4a80-42d8-b740-f7e7c7ef0b14.png",
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/14ed90d3-ff3c-491f-9efb-2a1b15f69d7f.png"
    ],
    "author_id": 6,
    "author_account_id": "test123",
    "author_username": "testuser",
    "author_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "hashtags": [
        {
            "id": 1,
            "name": "열대어"
        },
        {
            "id": 2,
            "name": "소형"
        }
    ],
    "like_count": 0,
    "comment_count": 0,
    "view_count": 1,
    "created_at": "2025-11-17T14:20:18.334643+09:00",
    "updated_at": "2025-11-17T14:21:30.012338+09:00",
    "is_blurred": false,
    "is_deleted": false,
    "report_count": 0
}
```

#### 비고
- 존재하지 않는 게시글 조회 시 HTTPException 발생


### 4. PATCH `/api/posts/{post_id}`
- **설명** : 사용자 본인의 게시글 수정
    - 이미지, 해시태그 수정 가능

#### Request

- **Headers**
    - `Content-Type` : multipart/form-data
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |

-> url 구조는 `/api/posts/2`가 됨.

- **Body** : PostUpdate
    - form-data

    | key | type | example |
    |------|------|----------|
    | title | text | `제목이 수정된 게시글` |
    | content | text | `이 게시글은 수정되었습니다` |
    | images  | file | [`image3.png`, `image4.png`] |
    | hashtags | text | [`수정된 태그`, `새로 추가된 태그`] |

    - 모든 필드는 **optional**

#### Response
- PostDetailResponse (정상 응답 시)
```json
{
    "id": 2,
    "title": "제목이 수정된 게시글",
    "content": "이 게시글은 수정되었습니다",
    "image_urls": [
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/7178fc98-bb48-4152-af4c-ff9e353cb8e4.png",
        "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/posts/7a5885dd-9021-4ddd-9cd0-53fda46a323e.png"
    ],
    "author_id": 6,
    "author_account_id": "test123",
    "author_username": "testuser",
    "author_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "hashtags": [
        {
            "id": 4,
            "name": "수정된 태그"
        },
        {
            "id": 5,
            "name": "새로 추가된 태그"
        }
    ],
    "like_count": 0,
    "comment_count": 0,
    "view_count": 1,
    "created_at": "2025-11-17T14:20:18.334643+09:00",
    "updated_at": "2025-11-17T14:22:42.314093+09:00",
    "is_blurred": false,
    "is_deleted": false,
    "report_count": 0
}
```

#### 비고
- 제공된 필드만 업데이트됨.
- 사용자 본인이 작성하지 않은 게시글을 수정하려고 하면 HTTPException 발생


### 5. DELETE `/api/posts/{post_id}`
- **설명** : 본인 게시글 삭제

#### Request

- **Headers**
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 3 |

-> url 구조는 `/api/products/3`가 됨.

#### Response

- 정상 응답 시
```json
{
    "detail": "게시글이 삭제되었습니다."
}
```

#### 비고
- 본인이 작성하지 않은 게시글을 삭제 시도 시 HTTPException 발생
- 실제 게시글 삭제가 아닌, Soft Delete 방식(is_deleted=True 처리)


### 6. POST `/api/posts/{post_id}/likes`
- **설명** : 특정 게시글 좋아요 등록

#### Request

- **Headers**
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |

-> url 구조는 `/api/posts/2/likes`가 됨.

#### Response

- 정상 응답 시
```json
{
    "detail": "게시글 좋아요가 등록되었습니다."
}
```

#### 비고
- 이미 좋아요한 게시글에 대해 좋아요 등록 시도 시 HTTPException 발생
- 본인이 작성한 게시글에 대해 좋아요 등록도 가능


### 7. DELETE `/api/posts/{post_id}/likes`
- **설명** : 특정 게시글 좋아요 취소

#### Request

- **Headers**
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |

-> url 구조는 `/api/posts/2/likes`가 됨.

#### Response

- 정상 응답 시
```json
{
    "detail": "게시글 좋아요가 취소되었습니다."
}
```

#### 비고
- 좋아요 등록하지 않은 게시글을 좋아요 취소 시도할 경우 HTTPException 발생


### 8. GET `/api/posts/{post_id}/likes`
- **설명** : 특정 게시글 좋아요한 사용자 목록 조회

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |

-> url 구조는 `/api/posts/2/likes`가 됨.

#### Response

- UserListItem[] (정상 응답 시)
```json
[
    {
        "id": 6,
        "account_id": "test123",
        "username": "testuser",
        "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg"
    }
]
```

### 비고
- 해당 게시글에 좋아요한 사용자가 없으면 빈 배열 `[]` 반환


## Comment

### 1. POST `/api/posts/{post_id}/comments`
- **설명** : 특정 게시글에 댓글 작성

#### Request

- **Headers**
    - `Content-Type` : application/json
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |

-> url 구조는 `/api/posts/2/comments`가 됨.

- **Body** : CommentCreate

    - raw
    ```json
    {
        "content" : "첫 번째 댓글입니다."
    }
    ```

#### Response

- CommentResponse (정상 응답 시)
```json
    {
        "id": 1,
        "post_id": 2,
        "user_id": 6,
        "username": "testuser",
        "account_id": "test123",
        "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "content": "첫 번째 댓글입니다.",
        "parent_comment_id": null,
        "created_at": "2025-11-18T00:40:34.820944+09:00",
        "updated_at": "2025-11-18T00:40:34.820944+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0,
        "replies": []
    }
```

#### 비고
- 존재하지 않는 게시글에 댓글 작성하려 할 경우 HTTPException 발생


### 2. GET `/api/posts/{post_id}/comments`
- **설명** : 특정 게시글의 댓글 목록 조회
    - 응답에는 댓글, 대댓글이 모두 포함됨.

#### Request

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |

-> url 구조는 `/api/posts/2/comments`가 됨.

#### Response

- CommentResponse[] (정상 응답 시)
```json
[
    {
        "id": 1,
        "post_id": 2,
        "user_id": 6,
        "username": "testuser",
        "account_id": "test123",
        "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "content": "첫 번째 댓글입니다.",
        "parent_comment_id": null,
        "created_at": "2025-11-18T00:40:34.820944+09:00",
        "updated_at": "2025-11-18T00:40:34.820944+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0,
        "replies": []
    },
    {
        "id": 2,
        "post_id": 2,
        "user_id": 6,
        "username": "testuser",
        "account_id": "test123",
        "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
        "content": "두 번째 댓글입니다.",
        "parent_comment_id": null,
        "created_at": "2025-11-18T00:40:46.395370+09:00",
        "updated_at": "2025-11-18T00:40:46.395370+09:00",
        "is_blurred": false,
        "is_deleted": false,
        "report_count": 0,
        "replies": []
    }
]
```

#### 비고
- 존재하지 않는 게시글에 대해 댓글 목록 조회 시 HTTPException 발생
- 댓글이 없으면 빈 배열 `[]` 반환


### 3. PATCH `/api/posts/{post_id}/comments/{comment_id}`
- **설명** : 댓글 내용 수정 (댓글 작성자 본인만 가능)

#### Request

- **Headers**
    - `Content-Type` : application/json
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |
| comment_id | 1 |

-> url 구조는 `/api/posts/2/comments/1`가 됨.

- **Body** : CommentUpdate

    - raw
    ```json
    {
        "content" : "이 댓글은 수정되었습니다."
    }
    ```

#### Response

- CommentResponse (정상 응답 시)
```json
{
    "id": 1,
    "post_id": 2,
    "user_id": 6,
    "username": "testuser",
    "account_id": "test123",
    "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "content": "이 댓글은 수정되었습니다.",
    "parent_comment_id": null,
    "created_at": "2025-11-18T00:40:34.820944+09:00",
    "updated_at": "2025-11-18T00:41:22.045239+09:00",
    "is_blurred": false,
    "is_deleted": false,
    "report_count": 0,
    "replies": []
}
```

#### 비고
- 사용자 본인이 작성하지 않은 댓글을 수정하려 시도할 경우 HTTPException 발생
- 존재하지 않는 댓글을 수정하려 시도할 경우 HTTPException 발생


### 4. DELETE `/api/posts/{post_id}/comments/{comment_id}`
- **설명** : 특정 댓글 삭제 (작성자 본인만 가능)
    - 삭제하려는 댓글에 대댓글이 존재한다면, 대댓글까지 삭제

#### Request

- **Headers**
    - `Content-Type` : application/json
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |
| comment_id | 2 |

-> url 구조는 `/api/posts/2/comments/2`가 됨.

#### Response

- 정상 응답 시
```json
{
    "detail": "댓글이 삭제되었습니다."
}
```

#### 비고
- 본인이 작성하지 않은 댓글을 삭제 시도 시 HTTPException 발생
- 실제 댓글 삭제가 아닌, Soft Delete 방식(is_deleted=True 처리). 대댓글도 Soft Delete 방식으로 처리함.
    - post의 comment_count는 삭제하는 댓글, 대댓글 수만큼 감소함.


### 5. POST `/api/posts/{post_id}/comments/{comment_id}/replies`
- **설명** : 특정 댓글에 대댓글 작성

#### Request

- **Headers**
    - `Content-Type` : application/json
    - `Authorization` : bearer `<access_token>`

- **Path Parameter**

| key | example |
| --- | ------- |
| post_id | 2 |
| comment_id | 2 |

-> url 구조는 `/api/posts/2/comments/2/replies`가 됨.

- **Body** : CommentCreate

    - raw
    ```json
    {
        "content" : "이것은 대댓글입니다."
    }
    ```

#### Response

- CommentResponse (정상 응답 시)
```json
{
    "id": 4,
    "post_id": 2,
    "user_id": 6,
    "username": "testuser",
    "account_id": "test123",
    "profile_image_url": "https://fish-market-files.s3.ap-northeast-2.amazonaws.com/profile-images/b7d20faa-726c-4c89-8848-5a505cd41bd7.jpg",
    "content": "이것은 대댓글입니다.",
    "parent_comment_id": 2,
    "created_at": "2025-11-18T00:41:55.251528+09:00",
    "updated_at": "2025-11-18T00:41:55.251528+09:00",
    "is_blurred": false,
    "is_deleted": false,
    "report_count": 0,
    "replies": []
}
```

#### 비고
- 존재하지 않는 댓글에 대댓글 작성하려 할 경우 HTTPException 발생