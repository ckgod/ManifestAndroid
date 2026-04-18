# Details: Retrofit CallAdapter

## Retrofit의 CallAdapter란? {#what-is-call-adapter}

Retrofit의 [CallAdapter](https://square.github.io/retrofit/2.x/retrofit/retrofit2/CallAdapter.html)는 Retrofit API 메서드의 반환 타입을 변환할 수 있도록 만들어진 추상화입니다. 기본적으로 Retrofit API 메서드는 `Call<T>` 객체를 반환합니다. `Call<T>`는 동기·비동기 모두로 실행할 수 있는 HTTP 요청을 나타냅니다. 그런데 **CallAdapter** 를 사용하면 이 기본 반환 타입을 LiveData, Flow, RxJava 타입, 혹은 사용자 정의 타입처럼 다른 형태로 변환할 수 있습니다.

CallAdapter 덕분에 Retrofit은 리액티브 프로그래밍이나 코루틴 기반 접근처럼 다양한 패러다임이나 라이브러리와 자연스럽게 결합할 수 있습니다.

### CallAdapter의 동작 방식 {#how-it-works}

Retrofit은 `CallAdapter.Factory`를 통해 `CallAdapter` 인스턴스를 생성합니다. `CallAdapter`는 `Call<T>` 객체를 원하는 타입으로 변환하는 일을 런타임에 수행합니다. 이 변환은 Retrofit이 API 인터페이스에 대한 프록시(proxy)를 만드는 시점에 일어납니다.

### Retrofit 기본 CallAdapter {#default-call-adapter}

기본적으로 Retrofit은 `Call<T>` 객체를 그대로 반환하는 CallAdapter를 포함합니다. 다른 타입을 반환하려면 적절한 라이브러리를 추가하거나 직접 CallAdapter를 작성해야 합니다.

### 예시: 코루틴용 CallAdapter 사용하기 {#using-coroutine-call-adapter}

Kotlin에서 Retrofit API 인터페이스에 `suspend` 수정자를 사용할 수 있게 해 주는 어댑터가 **Kotlin Coroutines Adapter** 입니다. `Call<T>`를 반환하는 대신 실제 결과를 반환하거나, 오류 시 예외를 던지도록 메서드의 모양을 바꿔 줍니다.

```kotlin
interface ExampleApi {
    @GET("users")
    suspend fun getUsers(): List<User>
}
```
{title="ExampleApi.kt"}

이 경우 Retrofit은 내부적으로 CallAdapter를 사용해 `Call<List<User>>`를 `List<User>`를 반환하는 `suspend` 함수로 바꿔 줍니다.

### 커스텀 CallAdapter 예시 {#custom-call-adapter}

Retrofit과 LiveData를 결합하고 싶다면 다음과 같이 커스텀 CallAdapter를 만들 수 있습니다.

```kotlin
class LiveDataCallAdapter<T>(
    private val responseType: Type
) : CallAdapter<T, LiveData<T>> {
    override fun responseType() = responseType

    override fun adapt(call: Call<T>): LiveData<T> {
        return object : LiveData<T>() {
            override fun onActive() {
                super.onActive()
                call.enqueue(object : Callback<T> {
                    override fun onResponse(call: Call<T>, response: Response<T>) {
                        value = response.body()
                    }

                    override fun onFailure(call: Call<T>, t: Throwable) {
                        // 실패 처리
                    }
                })
            }
        }
    }
}

class LiveDataCallAdapterFactory : CallAdapter.Factory() {
    override fun get(
        returnType: Type,
        annotations: Array<Annotation>,
        retrofit: Retrofit
    ): CallAdapter<*, *>? {
        if (getRawType(returnType) != LiveData::class.java) return null
        val observableType = getParameterUpperBound(0, returnType as ParameterizedType)
        return LiveDataCallAdapter<Any>(observableType)
    }
}
```
{title="LiveDataCallAdapter.kt"}

만든 어댑터를 사용하려면 Retrofit 빌더에 팩토리를 등록합니다.

```kotlin
val retrofit = Retrofit.Builder()
    .baseUrl("https://example.com/")
    .addCallAdapterFactory(LiveDataCallAdapterFactory())
    .addConverterFactory(GsonConverterFactory.create())
    .build()
```
{title="RetrofitSetup.kt"}

이제 API 메서드가 LiveData를 직접 반환할 수 있습니다.

```kotlin
interface ExampleApi {
    @GET("users")
    fun getUsers(): LiveData<List<User>>
}
```
{title="ExampleApi.kt"}

### 요약 {#summary}

<tldr>

Retrofit의 **CallAdapter** 는 기본 반환 타입인 `Call&lt;T&gt;`를 LiveData, Flow, RxJava observable, 사용자 정의 타입 등 다양한 형태로 변환할 수 있게 해 주는 메커니즘입니다. 덕분에 Retrofit을 선호하는 아키텍처나 라이브러리와 자연스럽게 결합할 수 있습니다. Retrofit은 `Call&lt;T&gt;`와 코루틴용 기본 CallAdapter를 포함하지만, 커스텀 어댑터를 만들면 특정 요구사항에 맞춘 더 고도화된 사용 사례에도 대응할 수 있습니다. 더 깊이 있는 활용은 *Modeling Retrofit Responses With Sealed Classes and Coroutines* 같은 자료를 참고하면 좋습니다.

</tldr>
