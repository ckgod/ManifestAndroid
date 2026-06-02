# Q72) REST API와 네트워크 통신

안드로이드 앱 대부분은 서버와 HTTP로 통신합니다. 이 토픽은 그 통신의 설계 원칙(REST)부터, 안드로이드에서 표준이 된 통신 라이브러리 스택(Retrofit + OkHttp), 공통 처리를 가로채는 Interceptor와 인증 헤더, 그리고 불안정한 네트워크를 견디는 타임아웃·재시도까지를 다룹니다.

## REST 원칙 {#rest-principles}

REST(Representational State Transfer)는 HTTP 위에서 자원(resource)을 다루는 **아키텍처 스타일**이지 프로토콜이나 표준이 아닙니다. 핵심은 **모든 것을 자원으로 보고, URL로 자원을 식별하며, HTTP 메서드로 그 자원에 대한 행위를 표현**한다는 것입니다.

- **자원 식별은 URL로**: `/users/42`는 42번 사용자라는 자원을 가리킵니다. URL에는 행위가 아니라 자원이 와야 합니다. `/getUser?id=42`가 아니라 `/users/42`입니다.
- **행위는 HTTP 메서드로**: 같은 `/users/42`에 대해 조회는 `GET`, 수정은 `PUT`/`PATCH`, 삭제는 `DELETE`입니다.
- **표현(representation)**: 서버는 자원의 상태를 JSON 같은 형식으로 표현해 주고받습니다. 같은 자원을 JSON으로도 XML로도 표현할 수 있습니다.

### HTTP 메서드와 그 성질 {#http-methods}

면접에서 자주 묻는 두 성질이 **안전성(safe)** 과 **멱등성(idempotent)** 입니다.

| 메서드 | 용도 | 안전성 | 멱등성 |
|--------|------|--------|--------|
| GET | 자원 조회 | O (서버 상태 변경 없음) | O |
| POST | 자원 생성 | X | X (호출마다 새 자원 생성 가능) |
| PUT | 자원 전체 교체 | X | O (같은 요청 여러 번 = 결과 동일) |
| PATCH | 자원 부분 수정 | X | △ (구현에 따라 다름) |
| DELETE | 자원 삭제 | X | O (이미 삭제된 것을 또 삭제해도 결과 동일) |

- **안전성**: 서버 상태를 바꾸지 않는 성질입니다. `GET`은 조회만 하므로 안전합니다.
- **멱등성**: 같은 요청을 여러 번 보내도 서버 상태가 한 번 보낸 것과 같은 성질입니다. 뒤에서 다룰 **재시도**가 안전한지를 가르는 기준이 바로 이 멱등성입니다. `POST`는 멱등이 아니므로 무턱대고 재시도하면 자원이 중복 생성될 수 있습니다.

### 무상태성(stateless) {#statelessness}

REST의 또 다른 핵심은 **무상태성**입니다. 서버는 요청 사이에 클라이언트의 상태를 저장하지 않으며, **각 요청은 그 요청을 처리하는 데 필요한 모든 정보를 스스로 담고 있어야** 합니다. 그래서 인증 정보(토큰)를 매 요청 헤더에 실어 보내야 합니다. 서버가 이전 요청의 클라이언트 상태를 보관하지 않기 때문입니다. 이 성질 덕분에 서버를 여러 대로 수평 확장하기 쉽습니다.

### 상태 코드 {#status-codes}

응답 결과는 HTTP 상태 코드로 구분합니다. 클라이언트는 이 코드로 분기 처리를 합니다.

- **2xx 성공**: 200 OK, 201 Created(생성됨), 204 No Content(성공이지만 본문 없음).
- **4xx 클라이언트 오류**: 400 Bad Request, 401 Unauthorized(인증 안 됨), 403 Forbidden(권한 없음), 404 Not Found.
- **5xx 서버 오류**: 500 Internal Server Error, 503 Service Unavailable.

이 분류가 중요한 이유는 **재시도 정책**과 직결되기 때문입니다. 4xx는 요청 자체가 잘못된 것이라 재시도해도 같은 결과지만, 5xx나 네트워크 단절은 일시적일 수 있어 재시도가 의미를 가집니다.

## Retrofit과 OkHttp {#retrofit-okhttp}

안드로이드 네트워킹의 사실상 표준 스택은 **Retrofit + OkHttp**입니다. 둘은 역할이 다릅니다.

- **OkHttp**: 실제 HTTP 통신을 담당하는 **저수준 HTTP 클라이언트**입니다. 소켓 연결, 커넥션 풀, HTTP/2, 캐시, 타임아웃, Interceptor 체인을 처리합니다.
- **Retrofit**: OkHttp 위에 올라가는 **타입 안전한 REST 클라이언트 추상화**입니다. 인터페이스에 애너테이션을 붙이면, Retrofit이 그 인터페이스의 구현체를 동적으로 생성해 HTTP 요청으로 바꿔 줍니다. 실제 통신은 내부의 OkHttp에 위임합니다.

즉 **Retrofit은 "어떤 요청을 보낼지"를 선언적으로 정의**하고, **OkHttp는 "그 요청을 실제로 어떻게 보낼지"를 담당**합니다.

### Retrofit 인터페이스 정의 {#retrofit-interface}

Retrofit에서는 API를 인터페이스로 선언합니다. 메서드 시그니처와 애너테이션이 곧 요청 명세입니다.

```kotlin
interface UserApi {
    @GET("users/{id}")
    suspend fun getUser(@Path("id") id: Long): User

    @GET("users")
    suspend fun searchUsers(@Query("q") keyword: String): List<User>

    @POST("users")
    suspend fun createUser(@Body request: CreateUserRequest): User
}
```

- `@GET`, `@POST`의 인자는 baseUrl에 이어 붙는 **상대 경로**입니다.
- `@Path`는 URL 경로의 `{id}` 자리를, `@Query`는 쿼리 파라미터(`?q=...`)를, `@Body`는 요청 본문(직렬화될 객체)을 채웁니다.
- 반환 타입을 `suspend fun ... : User`로 두면, Retrofit이 코루틴을 지원해 호출 지점에서 일시 중단으로 결과를 받습니다. `suspend` 없이 `Call<User>`로 받을 수도 있습니다.

### Retrofit 인스턴스 구성 {#retrofit-builder}

`Retrofit.Builder`로 baseUrl, JSON 변환기(converter), 그리고 통신을 담당할 OkHttp 클라이언트를 지정합니다.

```kotlin
val okHttpClient = OkHttpClient.Builder()
    .build()

val retrofit = Retrofit.Builder()
    .baseUrl("https://api.example.com/")   // 반드시 '/'로 끝나야 한다
    .client(okHttpClient)                  // 실제 통신을 담당할 OkHttp 주입
    .addConverterFactory(
        Json.asConverterFactory("application/json".toMediaType())
    )                                      // kotlinx.serialization 변환기
    .build()

val userApi: UserApi = retrofit.create(UserApi::class.java)
```

- **baseUrl은 `/`로 끝나야 합니다.** 그렇지 않으면 경로 결합 규칙 때문에 마지막 세그먼트가 잘려 의도와 다른 URL이 만들어집니다.
- **converter**가 JSON ↔ 코틀린 객체 변환을 맡습니다. 과거에는 Gson/Moshi를 많이 썼고, 지금은 `kotlinx.serialization`을 자주 씁니다.
- `client(okHttpClient)`를 생략하면 Retrofit이 기본 OkHttp 인스턴스를 만들지만, 실무에서는 Interceptor·타임아웃을 붙이기 위해 직접 구성한 클라이언트를 주입합니다.

### 왜 이 분리가 좋은가 {#why-separation}

Retrofit이 OkHttp를 감싸는 구조의 장점은 **관심사 분리**입니다. API 명세 변경(엔드포인트 추가, 파라미터 변경)은 Retrofit 인터페이스만 고치면 되고, 통신 정책 변경(타임아웃, 헤더, 로깅, 재시도)은 OkHttp 클라이언트만 고치면 됩니다. 또한 OkHttp 클라이언트는 **하나를 만들어 공유**해야 합니다. 내부의 커넥션 풀과 스레드 풀을 재사용하기 위해서이며, 요청마다 새로 만들면 자원이 낭비됩니다.

## Interceptor와 인증 헤더 {#interceptor-auth}

**Interceptor**는 OkHttp가 제공하는, **모든 요청과 응답이 통과하는 가로채기 지점**입니다. 요청이 나가기 직전과 응답이 들어온 직후에 끼어들어 요청·응답을 관찰하거나 변형할 수 있습니다. 인증 헤더 주입, 로깅, 공통 헤더 추가 같은 **횡단 관심사**를 여기서 한 곳에 모읍니다.

Interceptor는 **체인(chain)** 구조로 동작합니다. 각 Interceptor는 `chain.proceed(request)`를 호출해 다음 단계로 요청을 넘기고, 그 반환값으로 응답을 받습니다. 이 호출 전후가 각각 요청 전처리·응답 후처리 지점입니다.

### 인증 헤더 주입 {#auth-header-injection}

무상태성 때문에 매 요청에 인증 토큰을 헤더로 실어야 한다고 했습니다. 이를 매 API 호출마다 수동으로 넣으면 누락되기 쉬우므로, Interceptor에서 **모든 요청에 일괄로** 붙입니다.

```kotlin
class AuthInterceptor(
    private val tokenProvider: TokenProvider
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val request = original.newBuilder()
            .header("Authorization", "Bearer ${tokenProvider.accessToken()}")
            .build()
        return chain.proceed(request)   // 변형된 요청을 다음 단계로
    }
}
```

`Request`는 불변(immutable)이므로 직접 수정할 수 없고, `newBuilder()`로 복사본을 만들어 헤더를 추가한 뒤 그 새 요청을 `proceed`에 넘깁니다.

### Application vs Network Interceptor {#interceptor-types}

OkHttp의 Interceptor는 체인에서의 위치에 따라 두 종류로 나뉩니다. 이 차이가 면접에서 자주 나옵니다.

| 구분 | Application Interceptor | Network Interceptor |
|------|-------------------------|---------------------|
| 등록 메서드 | `addInterceptor` | `addNetworkInterceptor` |
| 호출 횟수 | 논리적 요청당 1번 | 실제 네트워크 요청당 (리다이렉트·재시도 시 여러 번) |
| 캐시된 응답 | 캐시 히트 시에도 실행됨 | 캐시 히트 시 실행 안 됨(네트워크를 안 타므로) |
| 적합한 용도 | 인증 헤더, 공통 헤더, 앱 레벨 로깅 | 실제 전송된 바이트·리다이렉트 관찰, 네트워크 레벨 디버깅 |

인증 헤더 주입은 보통 **Application Interceptor**로 둡니다. 리다이렉트마다 중복 실행될 필요가 없고, 논리적 요청 단위로 한 번만 토큰을 붙이면 되기 때문입니다.

### Interceptor vs Authenticator {#authenticator}

토큰 갱신(refresh)에서 중요한 구분이 있습니다. 위의 `AuthInterceptor`는 토큰을 **선제적으로** 붙입니다. 하지만 토큰이 만료되어 서버가 **401 Unauthorized**를 돌려준 경우, 토큰을 갱신해 자동 재요청하려면 OkHttp의 **`Authenticator`**를 쓰는 편이 적합합니다.

```kotlin
class TokenAuthenticator(
    private val tokenProvider: TokenProvider
) : Authenticator {
    override fun authenticate(route: Route?, response: Response): Request? {
        // 401이 왔을 때만 OkHttp가 이 메서드를 호출한다
        val newToken = tokenProvider.refreshToken() ?: return null  // null이면 포기
        return response.request.newBuilder()
            .header("Authorization", "Bearer $newToken")
            .build()   // 이 요청으로 OkHttp가 자동 재시도
    }
}
```

`Authenticator`는 **401 응답을 받았을 때만** OkHttp가 호출하며, 반환한 요청으로 자동 재시도합니다. `null`을 반환하면 재시도를 포기합니다. 매 요청에 무조건 토큰을 붙이는 일은 Interceptor가, 만료에 반응해 갱신·재시도하는 일은 Authenticator가 맡는 식으로 역할을 나눕니다.

```kotlin
val client = OkHttpClient.Builder()
    .addInterceptor(AuthInterceptor(tokenProvider))   // 선제적 토큰 부착
    .authenticator(TokenAuthenticator(tokenProvider)) // 401 시 갱신·재시도
    .build()
```

## 타임아웃과 재시도 {#timeout-retry}

모바일 네트워크는 느리거나 끊기기 쉽습니다. 그래서 **응답이 영원히 오지 않는 상황을 막는 타임아웃**과, **일시적 실패를 견디는 재시도**가 필수입니다.

### 타임아웃의 세 종류 {#timeout-kinds}

OkHttp는 단계별로 세 가지 타임아웃을 구분합니다. 한 가지 값으로 뭉뚱그리지 않는 이유는 각 단계가 멈추는 원인이 다르기 때문입니다.

```kotlin
val client = OkHttpClient.Builder()
    .connectTimeout(10, TimeUnit.SECONDS)  // TCP 연결 수립까지
    .readTimeout(15, TimeUnit.SECONDS)     // 연결 후 응답 바이트 사이 최대 간격
    .writeTimeout(15, TimeUnit.SECONDS)    // 요청 바이트를 보내는 단계
    .callTimeout(30, TimeUnit.SECONDS)     // 호출 전체(연결+전송+수신)의 상한
    .build()
```

- **connectTimeout**: 서버와 TCP/TLS 연결을 맺기까지의 제한입니다. 서버가 죽었거나 네트워크가 불통이면 여기서 걸립니다.
- **readTimeout**: 연결된 뒤 응답 데이터가 도착하는 **바이트 사이 간격**의 제한입니다. 전체 응답 시간이 아니라 "다음 바이트가 이 시간 안에 와야 한다"는 의미입니다.
- **writeTimeout**: 요청 본문을 서버로 올려보내는 단계의 제한입니다(파일 업로드 등).
- **callTimeout**: 위 단계 전부를 포함한 **호출 한 건의 전체 상한**입니다. 0이면(기본) 무제한이며, 전체 시간을 통제하고 싶을 때 설정합니다.

타임아웃을 설정하지 않으면 OkHttp 기본값(각 10초, callTimeout은 0=무제한)이 적용됩니다. 기본 callTimeout이 무제한이므로, readTimeout이 계속 갱신되는 응답에서는 호출이 길게 늘어질 수 있어 실무에서는 callTimeout도 함께 두는 편이 안전합니다.

### 재시도: 무엇을, 언제 {#retry-policy}

재시도에서 가장 중요한 원칙은 **멱등하지 않은 요청을 함부로 재시도하지 않는다**는 것입니다. 위에서 본 것처럼 `POST`는 멱등이 아니므로, 네트워크 타임아웃 후 재시도하면 서버가 이미 처리했을 수 있어 자원이 중복 생성될 위험이 있습니다. 재시도는 다음 경우로 한정하는 것이 안전합니다.

- **멱등한 메서드**(GET, PUT, DELETE)의 실패
- **일시적 오류**: 네트워크 단절, 타임아웃, 5xx(특히 503)
- **재시도하면 안 되는 것**: 4xx(요청 자체가 잘못됨), 비멱등 POST

OkHttp는 `retryOnConnectionFailure(true)`(기본값)로 **연결 실패 수준의 재시도**는 자동 처리하지만, 응답 코드(5xx 등)에 따른 재시도는 직접 구현해야 합니다.

### 지수 백오프(exponential backoff) {#exponential-backoff}

재시도를 즉시 반복하면 이미 부하를 받는 서버를 더 압박합니다. 그래서 재시도 간격을 **회차마다 지수적으로 늘리는** 지수 백오프를 씁니다. Interceptor로 구현하면 모든 요청에 일괄 적용할 수 있습니다.

```kotlin
class RetryInterceptor(private val maxRetry: Int = 3) : Interceptor {
    // 멱등한 메서드만 재시도 대상으로 둔다(POST 등 비멱등은 제외)
    private val idempotentMethods = setOf("GET", "PUT", "DELETE", "HEAD", "OPTIONS")

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        if (request.method !in idempotentMethods) {
            return chain.proceed(request)   // 비멱등 요청은 재시도하지 않고 한 번만 보낸다
        }
        var attempt = 0
        while (true) {
            try {
                val response = chain.proceed(request)
                // 5xx만 재시도, 4xx·2xx는 그대로 반환
                if (response.code < 500 || attempt >= maxRetry) return response
                response.close()                 // 재시도 전 응답 본문 반드시 닫기
            } catch (e: IOException) {            // 네트워크 단절·타임아웃
                if (attempt >= maxRetry) throw e
            }
            attempt++
            Thread.sleep(1000L * (1 shl (attempt - 1)))  // 1s, 2s, 4s ...
        }
    }
}
```

- `1 shl (attempt - 1)`은 2의 거듭제곱(1, 2, 4 ...)으로 대기 시간을 늘립니다.
- 실무에서는 여기에 **지터(jitter, 약간의 무작위 지연)** 를 더해, 동시에 실패한 클라이언트들이 같은 시각에 한꺼번에 재요청하는 쏠림을 분산시킵니다.
- 비동기 호출(`enqueue`)에서는 Interceptor 체인이 OkHttp의 백그라운드 스레드에서 실행되므로 `Thread.sleep`이 메인 스레드를 막지 않습니다. 다만 메인 스레드에서 동기 `execute`로 호출하면 체인이 호출 스레드에서 돌아 메인이 막히므로, 코루틴 환경이라면 호출부에서 `retryWhen`/`retry` 같은 코루틴 친화적 재시도를 쓰는 선택지도 있습니다.

## 요약 {#summary}

> **TL;DR** — REST는 자원을 URL로 식별하고 HTTP 메서드로 행위를 표현하는 무상태 아키텍처 스타일입니다. 안드로이드에서는 선언적 API 정의를 맡는 Retrofit과 실제 통신을 맡는 OkHttp를 함께 씁니다. 인증 헤더·로깅 같은 공통 처리는 Interceptor(401 갱신은 Authenticator)로 한 곳에 모으고, 불안정한 네트워크는 단계별 타임아웃과 멱등성에 근거한 지수 백오프 재시도로 견딥니다.

1. **REST 원칙**: 자원은 URL로 식별, 행위는 HTTP 메서드로 표현, 서버는 무상태. 메서드의 멱등성이 재시도 안전성을 가른다.
2. **Retrofit과 OkHttp**: Retrofit은 타입 안전한 선언적 API 추상화, OkHttp는 그 아래의 실제 HTTP 클라이언트. 둘의 분리가 명세 변경과 통신 정책 변경을 분리한다.
3. **Interceptor와 인증 헤더**: 모든 요청·응답을 통과하는 체인 지점. 토큰을 일괄 주입하고, 401 갱신·재시도는 Authenticator가 맡는다.
4. **타임아웃과 재시도**: connect/read/write/call로 단계별 타임아웃을 두고, 멱등하고 일시적인 실패에 한해 지수 백오프로 재시도한다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) REST에서 멱등성(idempotent)이란 무엇이고, 왜 네트워크 재시도와 관련이 있나요?">

멱등성은 같은 요청을 여러 번 보내도 서버 상태가 한 번 보낸 것과 동일하게 유지되는 성질입니다. GET, PUT, DELETE는 멱등이고 POST는 멱등이 아닙니다. 예를 들어 같은 PUT을 두 번 보내면 같은 값으로 두 번 교체하는 것이라 결과가 같지만, POST를 두 번 보내면 자원이 두 개 생길 수 있습니다.

이 성질이 재시도와 직결됩니다. 네트워크 타임아웃이 났을 때 요청이 서버에 도달해 처리됐는지, 아니면 아예 못 갔는지 클라이언트는 알 수 없습니다. 멱등한 요청은 이미 처리됐더라도 재시도가 안전하지만, 비멱등 POST를 재시도하면 결제·주문 같은 작업이 중복 실행될 수 있습니다. 그래서 재시도는 멱등한 메서드와 일시적 오류(네트워크 단절, 타임아웃, 5xx)로 한정하는 것이 안전합니다.

</def>
<def title="Q) Retrofit과 OkHttp는 각각 어떤 역할을 하나요? 왜 함께 쓰나요?">

OkHttp는 실제 HTTP 통신을 담당하는 저수준 클라이언트입니다. 소켓 연결, 커넥션 풀, HTTP/2, 캐시, 타임아웃, Interceptor 체인을 처리합니다. Retrofit은 그 위에 올라가는 타입 안전한 REST 추상화로, 애너테이션을 붙인 인터페이스를 동적 구현체로 만들어 HTTP 요청으로 바꿔 주고, 실제 전송은 내부 OkHttp에 위임합니다.

함께 쓰는 이유는 관심사 분리입니다. 엔드포인트나 파라미터 같은 API 명세 변경은 Retrofit 인터페이스만, 타임아웃·헤더·로깅·재시도 같은 통신 정책 변경은 OkHttp 클라이언트만 고치면 됩니다. 또한 OkHttp 클라이언트는 커넥션 풀과 스레드 풀을 재사용하기 위해 하나를 만들어 공유하고, 그것을 Retrofit에 주입하는 것이 권장됩니다.

</def>
<def title="Q) 모든 요청에 인증 토큰을 붙이려면 어떻게 하나요? 토큰 만료 시 자동 갱신은요?">

매 API 호출마다 토큰을 수동으로 넣으면 누락되기 쉬우므로, OkHttp Interceptor에서 일괄 처리합니다. `intercept`에서 `chain.request()`로 원본 요청을 받아 `newBuilder().header("Authorization", "Bearer ...")`로 토큰 헤더를 추가한 새 요청을 만들고, 그것을 `chain.proceed`로 넘깁니다. Request는 불변이므로 복사본을 만들어 변형합니다. 이 선제적 부착은 보통 Application Interceptor로 둡니다.

토큰 만료로 서버가 401을 돌려준 경우의 자동 갱신은 Interceptor보다 OkHttp의 Authenticator가 적합합니다. Authenticator는 401을 받았을 때만 OkHttp가 호출하며, 갱신한 토큰으로 만든 요청을 반환하면 OkHttp가 그 요청으로 자동 재시도하고, null을 반환하면 포기합니다. 즉 무조건 부착은 Interceptor, 만료 반응 갱신은 Authenticator로 역할을 나눕니다.

</def>
<def title="Q) OkHttp의 connectTimeout, readTimeout, callTimeout은 각각 무엇을 제한하나요?">

connectTimeout은 서버와 TCP/TLS 연결을 맺기까지의 제한입니다. 서버가 죽었거나 네트워크가 불통이면 여기서 걸립니다. readTimeout은 연결된 뒤 응답 데이터가 도착하는 바이트 사이 간격의 제한으로, 전체 응답 시간이 아니라 다음 바이트가 이 시간 안에 와야 한다는 의미입니다. writeTimeout은 요청 본문을 올려보내는 단계의 제한입니다.

callTimeout은 연결·전송·수신을 모두 포함한 호출 한 건 전체의 상한입니다. 기본값이 0(무제한)이므로, readTimeout이 계속 갱신되는 응답에서는 호출이 길게 늘어질 수 있습니다. 따라서 전체 시간을 통제하려면 callTimeout도 함께 설정하는 것이 안전합니다.

</def>
<def title="Q) 네트워크 재시도를 구현할 때 지수 백오프를 쓰는 이유는 무엇인가요?">

재시도를 즉시 반복하면 이미 과부하나 장애를 겪는 서버를 더 압박해 회복을 방해합니다. 지수 백오프는 재시도 간격을 회차마다 지수적으로(예: 1초, 2초, 4초) 늘려, 서버에 회복할 시간을 주면서 재시도를 시도합니다.

여기에 더해 지터(약간의 무작위 지연)를 섞는 것이 좋습니다. 동시에 실패한 여러 클라이언트가 똑같이 1초, 2초 뒤에 일제히 재요청하면 같은 시각에 트래픽이 몰리는 쏠림이 생기는데, 무작위 지연을 더하면 그 시점을 분산시킬 수 있습니다. 또한 재시도 대상은 멱등하고 일시적인 실패(GET/PUT/DELETE의 네트워크 단절·타임아웃·5xx)로 한정하고, 4xx나 비멱등 POST는 재시도하지 않는 것이 원칙입니다.

</def>
</deflist>
