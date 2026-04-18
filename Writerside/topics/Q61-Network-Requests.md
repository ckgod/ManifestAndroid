# Q61) 네트워크 요청 처리

## 데이터를 가져오기 위한 네트워크 요청을 어떻게 처리하나요? {#how-to-handle-network-requests}

Android 개발에서 네트워크 요청은 보통 [Retrofit](https://square.github.io/retrofit/)과 [OkHttp](https://square.github.io/okhttp/) 두 라이브러리를 함께 사용해 처리합니다. Retrofit은 선언적인 인터페이스로 API 호출을 간결하게 정의할 수 있도록 도와주고, OkHttp는 그 아래에서 동작하는 HTTP 클라이언트 역할을 맡으며 커넥션 풀링, 캐싱, 효율적인 통신을 담당합니다.

### Retrofit으로 네트워크 요청 만들기 {#using-retrofit}

Retrofit은 HTTP 요청을 깔끔하고 타입 안전한 API 인터페이스 형태로 추상화합니다. Gson이나 Moshi 같은 직렬화 라이브러리와도 자연스럽게 결합되어 JSON 응답을 Kotlin/Java 객체로 변환해 줍니다.

Retrofit으로 데이터를 가져오는 절차는 보통 세 단계로 나눠집니다.

1. **API 인터페이스 정의**: 어노테이션으로 엔드포인트와 HTTP 메서드를 선언합니다.

```kotlin
interface ApiService {
    @GET("data")
    suspend fun fetchData(): Response<DataModel>
}
```
{title="ApiService.kt"}

2. **Retrofit 인스턴스 구성**: base URL과 JSON 변환을 담당하는 컨버터 팩토리를 함께 설정합니다.

```kotlin
val retrofit = Retrofit.Builder()
    .baseUrl("https://api.example.com/")
    .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
    .build()

val apiService = retrofit.create(ApiService::class.java)
```
{title="RetrofitInstanceSetup.kt"}

3. **네트워크 호출 수행**: 코루틴을 사용해 비동기로 API를 호출합니다.

```kotlin
viewModelScope.launch {
    try {
        val response = apiService.fetchData()
        if (response.isSuccessful) {
            val data = response.body()
            Log.d(TAG, data.toString())
        } else {
            Log.d(TAG, "Error: ${response.code()}")
        }
    } catch (e: Exception) {
        e.printStackTrace()
    }
}
```
{title="MakingNetworkRequest.kt"}

### OkHttp로 직접 HTTP 요청 다루기 {#using-okhttp}

OkHttp는 Retrofit보다 더 직접적인 방식으로 HTTP 요청을 다룰 수 있게 해 줍니다. 헤더, 캐싱 같은 부분을 정밀하게 제어해야 할 때 유용합니다.

```kotlin
val client = OkHttpClient()

val request = Request.Builder()
    .url("https://api.example.com/data")
    .build()

client.newCall(request).enqueue(object : Callback {
    override fun onFailure(call: Call, e: IOException) {
        e.printStackTrace()
    }

    override fun onResponse(call: Call, response: Response) {
        if (response.isSuccessful) {
            Log.d(TAG, response.body?.string().orEmpty())
        } else {
            Log.d(TAG, "Error: ${response.code}")
        }
    }
})
```
{title="OkHttpGetRequest.kt"}

### Retrofit과 OkHttp 결합 {#integrating-okhttp-with-retrofit}

Retrofit은 내부적으로 OkHttp를 HTTP 클라이언트로 사용합니다. 그래서 Retrofit에 커스텀 OkHttpClient를 주입해 인터셉터로 로깅, 인증, 캐싱 같은 동작을 자유롭게 추가할 수 있습니다.

```kotlin
val okHttpClient = OkHttpClient.Builder()
    .addInterceptor { chain ->
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer your_token")
            .build()
        chain.proceed(request)
    }
    .build()

val retrofit = Retrofit.Builder()
    .baseUrl("https://api.example.com/")
    .client(okHttpClient)
    .addConverterFactory(GsonConverterFactory.create())
    .build()
```
{title="CustomOkHttpClientWithRetrofit.kt"}

이런 구성으로 인증 토큰 부착, 디버깅용 상세 로깅 같은 기능을 손쉽게 추가할 수 있습니다.

### 요약 {#summary}

<tldr>

Retrofit과 OkHttp를 함께 사용하면 Android에서 네트워크 요청을 견고하게 처리할 수 있습니다. Retrofit은 HTTP 호출의 정의와 실행을 단순화해 주고, OkHttp는 네트워크 동작을 세밀하게 커스터마이즈할 수 있는 유연성을 제공합니다. 두 라이브러리를 함께 쓰면 효율적이고 유지보수하기 좋은 네트워킹 레이어를 만들 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 여러 API 요청을 동시에 보내고 결과를 모은 다음 UI를 갱신해야 한다면 Retrofit과 코루틴으로 어떻게 효율적으로 구현하시겠습니까?">

가장 자연스러운 패턴은 코루틴의 `async`/`await`를 사용해 여러 요청을 병렬로 시작한 뒤, 모든 결과가 도착한 시점에서 한꺼번에 합치는 것입니다. Retrofit의 `suspend fun`이 반환하는 결과를 `coroutineScope { ... }` 안에서 `async`로 감싸면, 각 요청은 별도의 자식 코루틴에서 동시에 실행되고 `await()` 시점에 결과를 모을 수 있습니다. 예를 들어 `val (a, b) = listOf(async { api.fetchA() }, async { api.fetchB() }).awaitAll()` 형태로 두 응답을 모두 받은 뒤 ViewModel의 StateFlow에 결합 결과를 발행하는 식입니다.

여기서 중요한 점은 자식 코루틴이 같은 스코프를 공유한다는 것입니다. 한 요청이 실패해 예외를 던지면 같은 `coroutineScope` 블록 안의 다른 요청은 자동으로 취소됩니다. 일부 실패를 허용하고 나머지 결과만으로 화면을 그리고 싶다면 `supervisorScope`를 사용하거나, `runCatching`으로 각 `async` 결과를 감싸 실패를 값으로 처리하면 됩니다.

추가로 UI 갱신은 메인 디스패처에서 일어나야 하므로 ViewModel/Composable이 관찰하는 StateFlow나 LiveData에 결합 결과를 흘리는 형태가 가장 깔끔합니다. 네트워크 호출 자체는 Retrofit의 `suspend fun`이 이미 내부에서 적절한 디스패처로 전환해 주기 때문에, 호출자는 `Dispatchers.IO` 등을 명시적으로 지정하지 않아도 됩니다.

</def>
<def title="Q) API 실패와 재시도(retry) 메커니즘은 어떻게 처리하시겠습니까?">

API 실패는 크게 네트워크 단계의 일시 오류(타임아웃, 연결 끊김), HTTP 응답 단계의 클라이언트/서버 오류(4xx, 5xx), 그리고 인증 만료 같은 의미 단위 오류로 나누어 다루는 것이 좋습니다. 각각이 요구하는 처리 방식이 다르기 때문입니다.

일시적인 네트워크 오류와 5xx 같은 일시 서버 오류는 OkHttp 레벨에서 인터셉터로 재시도 정책을 거는 것이 가장 깔끔합니다. 코루틴 영역에서는 `suspend fun retry(times: Int, initialDelay: Long, factor: Double, block: suspend () -> T)` 같은 헬퍼를 만들어, 호출 결과가 실패했을 때 지수 백오프와 최대 재시도 횟수를 적용해 다시 시도하도록 만들 수 있습니다. 이 방식은 화면별로 재시도 정책을 다르게 가져갈 때도 유용합니다.

4xx 응답은 일반적으로 요청 자체가 잘못되었음을 의미하므로 재시도 대상이 아닙니다. 401 Unauthorized처럼 토큰 만료가 의심되는 경우에는 OkHttp의 `Authenticator`로 토큰 갱신 후 자동 재시도를 거는 패턴이 표준에 가깝습니다. 사용자 노출 측면에서는 마지막까지 실패한 경우에만 사용자에게 명시적인 에러 UI를 보여 주고, 그 안에 사용자 트리거 재시도 버튼을 두어 한 번 더 재시도할 수 있게 만드는 것이 좋습니다. 이렇게 하면 자동 재시도와 사용자 재시도가 자연스럽게 분리되어 동작합니다.

</def>
</deflist>
