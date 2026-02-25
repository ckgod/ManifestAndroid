# Q17) produceState

## produceState의 목적은 무엇이며 어떻게 동작하나요? {#what-is-produce-state}

`produceState`는 새로운 코루틴을 실행하여 그 결과를 `State` 객체로 만들어주는 함수입니다. Compose와 비동기적으로 가져오거나 계산하는 데이터 사이의 다리 역할을 하며, 비동기 작업에 의존하는 상태를 관리하거나 Compose 외부 상태를 Compose 상태로 변환할 때 특히 유용합니다. Composable이 Composition을 떠나면 코루틴 스코프가 자동으로 취소되어 리소스 누수를 방지합니다.

### 함수 시그니처 {#function-signature}

`produceState`의 함수 시그니처는 다음과 같습니다.

```kotlin
@Composable
fun <T> produceState(
    initialValue: T,
    vararg keys: Any?,
    producer: suspend ProduceStateScope<T>.() -> Unit
): State<T>
```
{title="ProduceState.kt"}

- **`initialValue`**: 프로듀서가 업데이트를 시작하기 전 상태의 초기값입니다.
- **`keys`**: 프로듀서의 의존성입니다. 키 값이 변경되면 프로듀서 코루틴이 재시작됩니다.
- **`producer`**: 상태 값을 업데이트하는 suspend 람다입니다.

### 사용 예시 {#usage-example}

네트워크에서 데이터를 가져오는 실제 사용 예시입니다.

```kotlin
@Composable
fun UserProfile(userId: String) {
    val userState by produceState<User?>(initialValue = null, userId) {
        value = fetchUserFromNetwork(userId)
    }

    if (userState == null) {
        Text("Loading...")
    } else {
        Text("User: ${userState?.name}")
    }
}

suspend fun fetchUserFromNetwork(userId: String): User {
    delay(2000) // 네트워크 지연 시뮬레이션
    return User(name = "skydoves")
}

data class User(val name: String)
```
{title="ProduceStateExample.kt"}

1. `produceState`로 초기값이 `null`인 `State<User?>` 객체를 생성합니다.
2. 프로듀서 코루틴이 비동기적으로 사용자 데이터를 가져와 `value`를 업데이트합니다.
3. 값이 변경되면 `UserProfile` Composable이 리컴포지션되어 최신 데이터를 표시합니다.

### produceState의 장점 {#benefits}

- **선언형**: 비동기 작업으로 상태를 만드는 Compose 고유의 깔끔한 방식을 제공합니다.
- **Composition 인식**: Composable이 Composition을 떠날 때 코루틴이 자동으로 취소되어 리소스 누수 위험이 줄어듭니다.
- **유연성**: 외부 suspend 함수와 잘 연동되며, 의존성 키(keys)가 변경될 때 재시작할 수 있습니다.

### 모범 사례 {#best-practices}

의미 있는 키를 사용하여 프로듀서 코루틴이 꼭 필요할 때만 재시작되도록 합니다. 또한, `withContext`로 코루틴 디스패처를 명시적으로 변경하지 않으면 `produceState`는 메인 스레드에서 실행됩니다. 따라서 무거운 작업이나 장시간 실행되는 작업은 `withContext(Dispatchers.IO)` 등으로 디스패처를 전환하여 메인 스레드 블로킹을 방지해야 합니다.

```kotlin
@Composable
fun DataScreen(query: String) {
    val result by produceState<List<Item>>(initialValue = emptyList(), query) {
        value = withContext(Dispatchers.IO) {
            repository.search(query) // IO 스레드에서 실행
        }
    }
    // ...
}
```
{title="ProduceStateBestPractice.kt"}

### 요약 {#summary}

<tldr>
`produceState`는 코루틴 작업을 실행하고 그 결과를 Composition을 인식하는 선언형 방식으로 상태화하는 사이드 이펙트 핸들러 API입니다. 코루틴으로 비동기 데이터 페칭을 수행하여 Compose UI에 통합하는 과정을 단순화해 줍니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Composable 함수에서 코루틴 작업을 실행하고 그 결과를 상태로 관찰해야 할 때, LaunchedEffect와 rememberCoroutineScope 없이 어떻게 구현할 수 있나요?">

`produceState`를 사용하면 됩니다. `produceState`는 내부적으로 `LaunchedEffect`를 활용하므로, 별도로 `LaunchedEffect`를 직접 작성하거나 `rememberCoroutineScope`로 스코프를 관리할 필요가 없습니다.

```kotlin
@Composable
fun SearchResults(query: String) {
    // LaunchedEffect와 rememberCoroutineScope 없이 코루틴 결과를 상태로 관찰
    val results by produceState<List<Item>>(initialValue = emptyList(), query) {
        value = withContext(Dispatchers.IO) {
            repository.search(query)
        }
    }

    LazyColumn {
        items(results) { item -> ItemRow(item) }
    }
}
```
{title="SearchResultsExample.kt"}

`query`를 키로 사용하므로 검색어가 변경될 때마다 프로듀서 코루틴이 재시작되어 최신 결과를 가져옵니다. Composable이 화면에서 사라지면 코루틴이 자동으로 취소됩니다.

</def>
</deflist>
