| 구분                              | HTTP   | Endpoint                          | 설명                              | 인증 |
| ------------------------------- | ------ | --------------------------------- | ------------------------------- | -- |
| **🔐 Auth (회원가입 / 로그인 / 탈퇴)**   |        |                                   |                                 |    |
|                                 | POST   | `/api/auth/signup`                | 회원가입 (email, password)          | ❌  |
|                                 | POST   | `/api/auth/login`                 | 로그인 (JWT 토큰 발급)                 | ❌  |
|                                 | POST   | `/api/auth/logout`                | 로그아웃 (JWT 무효화)                  | ✅  |
|                                 | DELETE | `/api/auth/withdraw`              | 회원 탈퇴                           | ✅  |
|                                 | POST   | `/api/auth/refresh`               | Refresh Token으로 새 Access Token 발급 | ❌ (Access Token 불필요, Refresh Token 필요) |
| **👤 User (프로필 / 팔로우 / 검색)**    |        |                                   |                                 |    |
|                                 | POST  | `/api/users/initial-profile`      | 초기 프로필 설정 (username, bio, 이미지 등) | ✅(임시 JWT)  |
|                                 | GET    | `/api/users/me`                   | 내 프로필 조회                        | ✅  |
|                                 | PATCH    | `/api/users/me`                   | 내 프로필 수정 (username, bio, 이미지 등) | ✅  |
|                                 | GET    | `/api/users/{user_id}`            | 특정 사용자 프로필 조회                   | ❌  |
|                                 | POST   | `/api/users/{user_id}/follow`     | 사용자 팔로우                         | ✅  |
|                                 | DELETE | `/api/users/{user_id}/follow`   | 사용자 언팔로우                        | ✅  |
|                                 | GET    | `/api/users/{user_id}/followers`  | 팔로워 목록                          | ❌  |
|                                 | GET    | `/api/users/{user_id}/followings` | 팔로잉 목록                          | ❌  |
|                                 | GET    | `/api/users/{user_id}/posts`       | 특정 사용자의 게시글 목록                  | ❌  |
|                                 | GET    | `/api/users/{user_id}/products`    | 특정 사용자의 상품 목록                   | ❌  |
|                                 | GET    | `/api/users/{user_id}/likes/posts`      | 특정 사용자가 좋아요한 게시글 목록 조회         | ❌  |
|                                 | GET    | `/api/users/{user_id}/likes/products`      | 특정 사용자가 좋아요한 상품 목록 조회            | ❌  |
|                                 | GET    | `/api/users/search?name=`        | 사용자 검색                          | ❌  |
| **🛍 Product (상품 등록 / 조회)**     |        |                                   |                                 |    |
|                                 | POST   | `/api/products`                   | 상품 등록 (이름, 가격, 설명, 이미지. 이미지 최소 1장~최대 5장)     | ✅  |
|                                 | GET    | `/api/products/{product_id}`      | 상품 상세 조회 (조회수/좋아요 수 포함)       | ❌  |
|                                 | PUT    | `/api/products/{product_id}`      | 상품 수정 (이름, 가격, 설명, 이미지)     | ✅  |
|                                 | DELETE   | `/api/products/{product_id}`   | 상품 삭제                       | ✅  |
|                                 | POST  | `/api/products/{product_id}/likes` | 상품 좋아요 등록           | ✅  |
|                                 | DELETE   | `/api/products/{product_id}/likes` | 상품 좋아요 취소        | ✅  |
| **📝 Post (게시글 / 피드)**          |        |                                   |                                 |    |
|                                 | GET    | `/api/posts/feed`                 | 홈 피드 (팔로잉 유저 게시글 최신순)           | ✅  |
|                                 | POST   | `/api/posts`                      | 게시글 작성 (텍스트, 해시태그, 이미지 최대 10장)         | ✅  |
|                                 | GET    | `/api/posts/{post_id}`            | 게시글 상세 조회 (조회수/좋아요 수/ 댓글 수 포함)     | ❌  |
|                                 | PATCH    | `/api/posts/{post_id}`            | 게시글 수정                          | ✅  |
|                                 | DELETE | `/api/posts/{post_id}`            | 게시글 삭제                          | ✅  |
|                                 | POST   | `/api/posts/{post_id}/likes`      | 게시글 좋아요 등록                      | ✅  |
|                                 | DELETE | `/api/posts/{post_id}/likes`      | 게시글 좋아요 취소                      | ✅  |
|                                 | GET    | `/api/posts/{post_id}/likes`      | 게시글 좋아요한 사용자 목록                 | ❌  |
| **💬 Comment (댓글)**             |        |                                   |                                 |    |
|                                 | POST   | `/api/posts/{post_id}/comments`   | 게시글에 댓글 작성                      | ✅  |
|                                 | GET    | `/api/posts/{post_id}/comments`   | 게시글 댓글 목록 조회                    | ❌  |
|                                 | PATCH    | `/api/posts/{post_id}/comments/{comment_id}`   | 댓글 수정                | ✅  |
|                                 | DELETE | `/api/posts/{post_id}/comments/{comment_id}`      | 댓글 삭제                           | ✅  |
|                                 | POST   | `/api/posts/{post_id}/comments/{comment_id}/replies`   | 대댓글 작성                  | ✅  |
| **💭 Chat (1:1 채팅)**            |        |                                   |                                 |    |
|                                 | GET    | `/api/chats`                      | 내가 참여 중인 모든 채팅방 목록을 조회. 각 채팅방에 ‘마지막 메시지’, ‘안읽은 메시지 수’를 포함하고, **‘마지막 메시지 도착 시간’을 기준으로 최신순 정렬**   | ✅  |
|                                 | POST   | `/api/chats`                | 새 채팅방 생성 (상대 user_id 필요)        | ✅  |
|                                 | GET    | `/api/chats/{chat_id}`            | 특정 채팅방의 메시지 목록 조회 (메시지별 읽음/안읽음 여부 포함)      | ✅  |
|                                 | PATCH | `/api/chats/{chat_id}/messages/{message_id}`  | 메시지 수정(텍스트/이미지)                        | ✅  |
|                                 | DELETE | `/api/chats/{chat_id}/messages/{message_id}` | 메시지 삭제                        | ✅  |
|                                 | DELETE | `/api/chats/{chat_id}`            | 채팅방 나가기                         | ✅  |
| 실시간 채팅 연결(HTTP 대신 WebSocket 이용) | WebSocket | `/ws/chats/{chat_id}`      | 채팅방에 연결하여 실시간 메시지 송수신 (텍스트/이미지) | ✅  |
| 　↳ `"send_message"`    | **Event (C→S)**      | —                      | 클라이언트가 서버에 새 메시지를 전송. 서버는 DB 저장 후, 상대방에게 `"receive_message"` 브로드캐스트       | ✅            |
| ↳ `"send_message_ack"` | **Event (S→C)**      | —                      | 서버가 메시지를 DB에 성공적으로 저장했음을 클라이언트에게 확인 응답 | ✅     |
| 　↳ `"receive_message"` | **Event (S→C)**      | —                      | 서버가 새 메시지를 해당 채팅방의 다른 사용자에게 전달                                            | ✅            |
| 　↳ `"read_message"`    | **Event (C→S)**      | —                      | 사용자가 특정 메시지를 읽었음을 서버에 알림 → 서버는 DB에 읽음 처리 후, 상대방에게 `"message_read_update"` 이벤트 전송 | ✅            |
| 　↳ `"message_read_update"`    | **Event (S→C)**      | —                      | 상대방이 메시지를 읽었음을 클라이언트에게 실시간 전달 (읽음 표시 업데이트용)                               | ✅            |
| **🚨 Report (신고)** *(선택)*       |        |                                   |                                 |    |
|                                 | POST   | `/api/reports`                    | 유저/게시글/댓글/채팅/상품 신고 등록           | ✅  |
| **🤝 Recommend (친구 추천)** *(선택)* |        |                                   |                                 |    |
|                                 | GET    | `/api/recommend/friends`          | 해시태그 기반 친구 추천                   | ✅  |
