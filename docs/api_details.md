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
    - 비밀번호 확인 후 Soft Delete (is_active=False). 해당 사용자의 계정 비활성화시킴.
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


