# Details: OkHttp Authenticator vs Interceptor로 OAuth 토큰 갱신하기

## OkHttp로 OAuth 토큰을 갱신하는 두 가지 방식 {#two-ways-to-refresh-token}

OAuth로 보호된 API를 다루다 보면 토큰 만료와 갱신 시나리오를 처리해야 할 때가 자주 있습니다. OkHttp는 토큰 갱신을 가로채고 처리할 수 있는 두 가지 메커니즘인 [Authenticator](https://square.github.io/okhttp/3.x/okhttp/okhttp3/Authenticator.html)와 [Interceptor](https://square.github.io/okhttp/features/interceptors/)를 제공합니다. 두 메커니즘은 목적이 다르며, 애플리케이션의 요구사항에 따라 적절한 쪽을 선택해야 합니다.

### OkHttp Authenticator 사용하기 {#using-authenticator}

OkHttp의 `Authenticator` 인터페이스는 인증 챌린지(authentication challenge)를 처리하기 위한 전용 후크입니다. 서버가 401 Unauthorized 상태 코드로 응답하면 `Authenticator`가 자동으로 호출되어, 갱신된 인증 정보로 요청을 다시 만들어 반환할 수 있습니다.

다음은 토큰 갱신을 위해 `Authenticator`를 구현하는 예시입니다.

```kotlin
class TokenAuthenticator(
    private val tokenProvider: TokenProvider
) : Authenticator {
    override fun authenticate(route: Route?, response: Response): Request? {
        // 토큰 프로바이더에서 새 토큰을 받아옵니다.
        val newToken = tokenProvider.refreshToken() ?: return null

        // 새 토큰으로 요청을 다시 만듭니다.
        return response.request.newBuilder()
            .header("Authorization", "Bearer $newToken")
            .build()
    }
}
```
{title="TokenAuthenticator.kt"}

`TokenProvider`는 토큰 갱신을 책임지는 커스텀 클래스로, 보통 갱신용 엔드포인트를 동기 호출하는 형태로 구현합니다. 이렇게 만든 `Authenticator`는 OkHttpClient 빌더에 등록해 사용합니다.

```kotlin
val okHttpClient = OkHttpClient.Builder()
    .authenticator(TokenAuthenticator(tokenProvider))
    .build()
```
{title="OkHttpClientSetup.kt"}

### OkHttp Interceptor 사용하기 {#using-interceptor}

`Interceptor`는 더 유연한 접근입니다. 토큰 부착과 갱신 로직을 모두 직접 다룰 수 있고, 요청과 응답을 처리되기 전에 들여다보고 수정할 수 있습니다.

일반적으로 응답의 401 상태 코드를 검사하고 인라인으로 토큰을 갱신하는 형태로 구현합니다.

```kotlin
class TokenInterceptor(
    private val tokenProvider: TokenProvider
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        // 요청에 토큰을 부착합니다.
        var request = chain.request().newBuilder()
            .header("Authorization", "Bearer ${tokenProvider.getToken()}")
            .build()

        // 요청을 진행시킵니다.
        val response = chain.proceed(request)

        // 토큰 만료 여부를 확인합니다.
        if (response.code == 401) {
            synchronized(this) {
                // 토큰을 갱신합니다.
                val newToken = tokenProvider.refreshToken() ?: return response
                // 새 토큰으로 요청을 다시 보냅니다.
                request = request.newBuilder()
                    .header("Authorization", "Bearer $newToken")
                    .build()
                return chain.proceed(request)
            }
        }
        return response
    }
}
```
{title="TokenInterceptor.kt"}

이 인터셉터는 OkHttpClient에 다음과 같이 등록합니다.

```kotlin
val okHttpClient = OkHttpClient.Builder()
    .addInterceptor(TokenInterceptor(tokenProvider))
    .build()
```
{title="OkHttpClientSetup.kt"}

### Authenticator와 Interceptor의 핵심 차이 {#key-differences}

1. **목적**: `Authenticator`는 인증 챌린지(보통 401 응답) 처리를 위해 설계된 전용 메커니즘입니다. 반면 `Interceptor`는 요청과 응답 처리 전반을 더 세밀하게 다루기 위한 범용 메커니즘입니다.
2. **자동 트리거**: `Authenticator`는 401 응답에 대해 자동으로 호출되지만, `Interceptor`는 401을 직접 감지해 갱신 로직을 트리거하는 코드를 작성해야 합니다.
3. **사용 시점**: 단순한 인증 챌린지 처리에는 `Authenticator`가, 요청·응답에 대한 복잡한 커스텀 처리에는 `Interceptor`가 더 적합합니다.

### 요약 {#summary}

<tldr>

OAuth 토큰 갱신은 서버가 보내는 401 챌린지를 자동으로 처리하기에는 `Authenticator`가, 토큰 관리 로직을 더 세밀하게 다루기에는 `Interceptor`가 적합합니다. 어느 쪽을 선택할지는 애플리케이션의 복잡도와 요구사항에 따라 달라집니다. 두 방식 모두 API 호출을 끊김 없이 이어 가면서 사용자 경험을 매끄럽게 유지하는 데 기여합니다.

</tldr>
