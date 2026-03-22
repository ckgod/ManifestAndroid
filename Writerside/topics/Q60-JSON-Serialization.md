# Q60) JSON 직렬화/역직렬화

## JSON을 객체로 어떻게 직렬화·역직렬화하나요? {#how-to-serialize-json}

JSON을 객체로 직렬화·역직렬화하는 작업은 Android 개발에서 매우 흔하게 마주치는 일입니다. 최신 Android 앱은 REST API, GraphQL 엔드포인트, Firebase 같은 원격 서버와 자주 상호작용하기 때문입니다. 이러한 서버는 가볍고 사람이 읽기 쉬우며 플랫폼에 종속되지 않는 JSON 형식을 데이터 교환의 표준으로 사용합니다.

사용자 데이터나 설정을 서버에 보내거나, 뉴스 기사·메시지처럼 콘텐츠를 받아 와야 할 때, 앱은 Kotlin 객체를 JSON으로 직렬화하고 서버 응답을 다시 사용 가능한 객체로 역직렬화해야 합니다.

### 직렬화와 역직렬화란? {#what-is-serialization}

- **직렬화(Serialization)**: 객체나 데이터 구조를 저장·전송·재구성하기 쉬운 형태로 변환하는 과정입니다. Android와 백엔드 통신의 맥락에서는 보통 객체를 JSON 문자열 같은 구조화된 포맷으로 바꾸는 작업을 의미합니다.
- **역직렬화(Deserialization)**: 그 반대 과정입니다. 직렬화된 데이터(예: JSON 문자열)를 받아 애플리케이션이 다룰 수 있는 인-메모리 객체로 다시 복원합니다.

### 수동 직렬화·역직렬화 {#manual-serialization}

직접 문자열을 조작해 객체를 JSON 문자열로 만들고, JSON 문자열에서 값을 파싱해 객체로 복원하는 식으로 수동 처리하는 것도 가능합니다.

수동 직렬화는 객체의 프로퍼티를 직접 끌어모아 JSON 문자열을 짜내는 방식입니다.

```kotlin
data class User(val name: String, val age: Int)

fun serializeUser(user: User): String {
    return """{
        "name": "${user.name}",
        "age": ${user.age}
    }""".trimIndent()
}

// 사용 예시
val user = User("John", 30)
val jsonString = serializeUser(user)
// 출력: {"name":"John","age":30}
```
{title="ManualSerialization.kt"}

수동 역직렬화는 JSON 문자열을 파싱해 값을 추출한 뒤 객체로 재구성합니다.

```kotlin
fun deserializeUser(json: String): User {
    val nameRegex = """"name"\s*:\s*"([^"]*)"""".toRegex()
    val ageRegex = """"age"\s*:\s*(\d+)""".toRegex()

    val name = nameRegex.find(json)?.groups?.get(1)?.value ?: ""
    val age = ageRegex.find(json)?.groups?.get(1)?.value?.toIntOrNull() ?: 0

    return User(name, age)
}

// 사용 예시
val jsonString = """{"name":"John","age":30}"""
val user = deserializeUser(jsonString)
// 출력: User(name="John", age=30)
```
{title="ManualDeserialization.kt"}

이 방식은 학습 목적이나 의존성을 최소화해야 하는 매우 가벼운 케이스에는 유용하지만, 유지보수성, 안전성, 확장성 측면에서 프로덕션 앱에는 권장되지 않습니다. 대신 **kotlinx.serialization**, **Moshi**, **Gson** 같은 라이브러리를 사용하면 JSON 문자열과 Kotlin/Java 객체 간 변환을 훨씬 효율적으로 처리할 수 있습니다.

### kotlinx.serialization {#kotlinx-serialization}

[kotlinx.serialization](https://github.com/Kotlin/kotlinx.serialization)은 JetBrains가 개발한 직렬화 라이브러리로 Kotlin 언어와 긴밀하게 통합되어 있습니다. 어노테이션으로 직렬화 동작을 정의하며, JSON뿐 아니라 ProtoBuf 같은 다른 포맷도 매끄럽게 지원합니다.

```kotlin
import kotlinx.serialization.*
import kotlinx.serialization.json.*

@Serializable
data class User(val name: String, val age: Int)

val json = """{"name": "John", "age": 30}"""
val user: User = Json.decodeFromString<User>(json) // JSON → 객체
val serializedJson: String = Json.encodeToString(user) // 객체 → JSON
```
{title="UsingKotlinxSerialization.kt"}

kotlinx.serialization은 최신 Android·Kotlin 개발에서 가장 선호되는 방식 중 하나입니다. Kotlin 컴파일러 플러그인을 활용해 타입 안전하고 리플렉션 없는(reflection-free) 변환 메커니즘을 제공하기 때문입니다. 내부적으로 컴파일러가 생성한 코드를 사용하므로, Moshi의 reflection 모드나 Gson과 달리 무거운 런타임 리플렉션이 필요하지 않습니다.

### Moshi {#moshi}

[Moshi](https://github.com/square/moshi)는 Square가 만든 모던 JSON 라이브러리로, 타입 안전성과 Kotlin 친화성을 강조합니다. Gson과 달리 **Kotlin의 nullability와 기본 파라미터(default parameters)** 를 기본 동작으로 지원하기 때문에, Kotlin 우선 개발에 더 적합합니다.

```kotlin
data class User(val name: String, val age: Int)

val moshi = Moshi.Builder().build()
val adapter = moshi.adapter(User::class.java)
val json = """{"name": "John", "age": 30}"""
val user = adapter.fromJson(json) // JSON → 객체
val serializedJson = adapter.toJson(user) // 객체 → JSON
```
{title="UsingMoshi.kt"}

Moshi에서 JSON 직렬화·역직렬화를 다루는 방식은 크게 두 가지로 나뉩니다. 둘 다 JSON과 Kotlin/Java 객체 간 변환을 가능하게 해 주지만, 성능·런타임 동작·내부 구현 측면에서 큰 차이를 보입니다.

- **Reflection-Based Moshi**: [reflection 기반 Moshi](https://github.com/square/moshi?tab=readme-ov-file#reflection)는 자바 리플렉션을 사용해 런타임에 동적으로 JSON 어댑터를 생성합니다. 별도의 설정이 거의 필요 없는 대신 런타임 오버헤드가 발생합니다.
- **Codegen-Based Moshi**: [codegen 기반 Moshi](https://github.com/square/moshi?tab=readme-ov-file#codegen)는 [Kotlin Symbol Processor(KSP)](https://kotlinlang.org/docs/ksp-overview.html)를 통한 어노테이션 처리로 컴파일 시점에 JSON 어댑터를 생성합니다. 그 결과 더 빠른 런타임 성능과 컴파일 단계에서의 오류 검사가 가능합니다.

reflection 기반 어댑터는 셋업이 빠르지만 런타임 성능 오버헤드와 멀티플랫폼 지원의 한계가 있습니다. codegen 방식은 컴파일 단계에서 최적화된 어댑터를 만들어 더 좋은 성능을 보이므로 일반적으로 codegen 방식이 더 권장됩니다.

> **추가 팁**: 커뮤니티에서 만든 [MoshiX](https://github.com/ZacSweers/MoshiX)라는 라이브러리도 있습니다. Kotlin IR(Intermediate Representation) 컴파일러 플러그인을 사용해 컴파일 시점에 고도로 최적화된 코드를 생성하므로, KSP 기반이나 reflection 기반보다 더 나은 성능을 기대할 수 있습니다.

### Gson {#gson}

[Gson](https://github.com/google/gson)은 Google이 개발한, 가장 널리 쓰여 온 JSON 라이브러리 중 하나입니다. 자바 객체를 JSON으로 직렬화하고 JSON을 자바 객체로 다시 역직렬화할 수 있으며, 단순한 API와 손쉬운 통합 덕분에 오랫동안 인기 있는 선택지였습니다.

```kotlin
data class User(val name: String, val age: Int)

val gson = Gson()
val json = """{"name": "John", "age": 30}"""
val user = gson.fromJson(json, User::class.java) // JSON → 객체
val serializedJson = gson.toJson(user) // 객체 → JSON
```
{title="UsingGson.kt"}

다만 Gson 대신 **kotlinx.serialization** 이나 **Moshi** 를 선택할 만한 분명한 이유들이 있습니다. 핵심 장점은 다음과 같습니다.

1. **더 나은 Kotlin 지원**: Gson은 Java를 전제로 설계된 라이브러리이기 때문에 기본 파라미터, val/var 구분, nullability 같은 Kotlin 고유 특성을 자연스럽게 다루지 못합니다.
2. **성능과 효율성**: kotlinx.serialization과 (특히 codegen을 사용한) Moshi는 런타임 리플렉션에 크게 의존하는 Gson보다 빠르고 메모리 효율도 더 좋습니다.
3. **멀티플랫폼 호환성**: kotlinx.serialization은 Kotlin Multiplatform(KMP)을 정식 지원하지만, Moshi와 Gson은 JVM에 묶여 있어 크로스 플랫폼 앱에는 적합하지 않습니다.
4. **컴파일 타임 안전성**: kotlinx.serialization과 codegen Moshi는 많은 오류를 컴파일 시점에 잡아내 런타임 크래시 가능성을 줄입니다. 반면 Gson은 같은 종류의 오류를 런타임에야 드러내는 경우가 많습니다.

Gson과 Moshi 모두에 기여한 Jake Wharton의 의견도 같은 맥락을 시사합니다. 그는 Reddit r/androiddev에서 다음과 같이 정리한 바 있습니다.

> Moshi는 사실상 이름만 다른 Gson v3에 가까워 마이그레이션이 가장 쉽다. Kotlin 지원에는 약간의 셋업이 필요하지만 어렵지는 않다. 단점은 거대한 의존성인 kotlin-reflect를 끌어 쓰거나 빌드 성능에 영향을 주는 코드 생성을 사용해야 한다는 점이다.
>
> kotlinx.serialization도 훌륭하다. 다만 Moshi(이미 Gson보다 기능이 적게 설계된)보다도 기능이 더 적은 대신, 멀티플랫폼처럼 흥미로운 가능성을 열어 준다. 단점은 현재 streaming을 지원하지 않아, 응답 본문이 매우 큰 경우 메모리 부담이 커질 수 있다는 점이다.
>
> 나는 모델을 JS와 공유해야 해서 멀티플랫폼이 필요하기 때문에 kotlinx.serialization을 사용한다.

### 요약 {#summary}

<tldr>
JSON을 객체로 직렬화·역직렬화할 때 Gson, Moshi, kotlinx.serialization은 모두 효율적인 매핑 API를 제공합니다. **kotlinx.serialization** 은 Kotlin 우선·멀티플랫폼 프로젝트에 최적이며 컴파일 타임 안전성, 가벼운 런타임, 네이티브 Kotlin 지원을 함께 누릴 수 있습니다. **Moshi** 는 빠른 성능과 안전한 JSON 처리가 필요한 Android 중심 앱에 적합하며, 특히 codegen 모드를 권장합니다. **Gson** 은 JVM 전용 빠른 통합에는 여전히 편리하지만 성능, Kotlin 지원, 최신 베스트 프랙티스 측면에서는 두 라이브러리에 비해 뒤처집니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) API에서 받은 JSON 응답을 Kotlin data class로 역직렬화하려면 어떻게 처리해야 하며, Kotlin 우선 프로젝트라면 어떤 라이브러리를 선택하시겠습니까?">

가장 자연스러운 방법은 data class를 정의하고, 선택한 라이브러리의 어노테이션으로 직렬화 정보를 부여한 뒤, Retrofit 같은 네트워크 레이어와 결합해 응답 변환을 라이브러리에 위임하는 것입니다. 예를 들어 kotlinx.serialization을 사용한다면 `@Serializable`을 붙인 data class를 정의하고 `Json.decodeFromString&lt;User&gt;(jsonString)` 형태로 변환하거나, Retrofit에 `kotlinx-serialization-converter`를 등록해 응답을 자동 매핑하게 만들 수 있습니다.

Kotlin 우선 프로젝트에서는 **kotlinx.serialization** 을 우선 후보로 두는 것이 합리적입니다. JetBrains가 직접 유지보수하기 때문에 Kotlin 언어 기능 변화와 호흡이 맞고, 컴파일러 플러그인이 직렬화 코드를 생성하므로 런타임 리플렉션 없이도 빠르고 타입 안전한 변환을 보장합니다. 또한 Kotlin Multiplatform을 정식 지원해 향후 코드 공유나 KMP 전환에도 유연하게 대응할 수 있습니다.

다만 라이브러리 선택은 단순한 성능 비교만이 아니라 팀의 익숙함과 생태계 의존성 문제로도 결정됩니다. 이미 Square 계열 라이브러리(OkHttp, Retrofit, Moshi)에 깊이 묶여 있는 코드베이스라면 codegen 모드를 켠 Moshi를 선택해도 합리적입니다. 신규 Kotlin 프로젝트, 특히 멀티플랫폼이 시야에 있다면 kotlinx.serialization이 가장 깔끔한 선택입니다.

</def>
<def title="Q) Kotlin data class에 정의되지 않은 필드가 JSON에 포함되어 있거나, JSON에 일부 필드가 누락된 상황은 어떻게 다뤄야 하나요?">

이 문제는 라이브러리마다 처리 방식이 조금씩 다르지만, 큰 그림은 같습니다. **모르는 필드는 무시하도록 설정** 하고, **누락 가능한 필드는 nullable이나 기본값으로 정의** 하는 것입니다.

kotlinx.serialization의 경우 추가 필드는 기본 동작으로 오류를 발생시키지만, `Json { ignoreUnknownKeys = true }` 같은 설정으로 안전하게 무시할 수 있습니다. 누락 필드는 data class의 프로퍼티에 기본값을 두면 자동으로 채워지고, 기본값 자리에 `null`을 두려면 nullable 타입(`String?` 등)으로 선언하면 됩니다. Moshi는 추가 필드를 기본적으로 무시하며, 누락 필드는 nullable 타입이거나 기본 파라미터를 가진 경우 안전하게 처리됩니다. Gson 역시 추가 필드는 무시하지만, Kotlin의 기본값과 nullability를 충실히 반영해 주지 못한다는 점이 약점이고, 이 부분이 Moshi/kotlinx.serialization을 선호하는 큰 이유 중 하나입니다.

스키마 변경에 대비하려는 경우라면 data class를 가능한 한 nullable과 기본값으로 방어적으로 설계하고, 서버 측 변경이 잦다면 별도의 응답 DTO를 두어 도메인 모델과 분리하는 것이 좋습니다. 이렇게 하면 새로운 필드가 들어와도 앱이 즉시 깨지지 않고, 누락된 필드도 명시적인 기본값/`null`로 안전하게 대체됩니다.

</def>
</deflist>
