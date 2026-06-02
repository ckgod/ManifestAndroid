# E2) Kotlin Flow

## Flow란 무엇인가 {#what-is-flow}

`Flow`는 **코루틴 위에서 동작하는 비동기 데이터 스트림** 타입입니다. `suspend` 함수가 값을 하나만 반환하는 데 비해, Flow는 **여러 값을 시간에 걸쳐 순차적으로 방출(emit)** 할 수 있습니다.

핵심 성질은 세 가지입니다.

- **비동기·논블로킹**: 값의 생성과 소비가 코루틴 위에서 일어나므로, 네트워크 요청처럼 시간이 걸리는 작업을 메인 스레드를 막지 않고 처리할 수 있습니다.
- **여러 값의 순차 방출**: `Iterator`처럼 값들의 시퀀스를 만들지만, 각 값 사이에서 `delay` 같은 `suspend` 호출로 일시 중단할 수 있다는 점이 다릅니다.
- **Cold**: Flow는 기본적으로 **cold** 입니다. `flow { }` 빌더로 만든 Flow는 수집(collect)을 시작하기 전까지 아무 코드도 실행하지 않습니다. collector가 붙는 순간 비로소 생산자 블록이 실행되고, **collector마다 독립적으로 처음부터 다시** 실행됩니다.

이 cold 특성이 뒤에서 다루는 Hot Flow(StateFlow·SharedFlow)와 대비되는 출발점입니다.

## 데이터 스트림의 구성 요소 {#stream-components}

Flow 기반 데이터 스트림은 세 가지 역할로 구성됩니다.

- **생산자(producer)**: 스트림에 데이터를 만들어 넣습니다. 코루틴 위에서 비동기로 값을 생성하며, 안드로이드에서는 보통 Repository가 네트워크·DB 데이터를 제공하는 역할을 맡습니다.
- **중개자(intermediary, 선택적)**: 스트림을 흘러가는 데이터를 변환하거나 걸러냅니다. `map`·`filter`·`transform` 같은 **중간 연산자(intermediate operator)** 를 쓰며, 값을 최종 소비하지 않고 가공만 합니다.
- **소비자(consumer)**: 스트림의 값을 최종적으로 수집해 사용합니다. `collect` 같은 **터미널 연산자(terminal operator)** 를 쓰며, 안드로이드에서는 ViewModel이 UI 상태를 갱신하는 위치입니다.

안드로이드 아키텍처에 대입하면 다음과 같습니다.

| 컴포넌트 | 역할 | 예시 |
|---------|------|------|
| Repository | UI 데이터의 생산자 | 네트워크·DB에서 데이터 제공 |
| UI Layer | 사용자 입력 이벤트의 생산자 | 클릭·텍스트 입력 등 |
| ViewModel | 중개자 + 소비자 | 데이터 변환 후 UI 상태 관리 |

![flow.png](flow.png)

## Flow 빌더 {#flow-builders}

Flow를 만드는 빌더는 크게 세 가지입니다.

- **`flow { }`**: 블록 안에서 `emit()`으로 값을 방출하는 가장 기본적인 빌더입니다. `emit`은 `suspend` 함수입니다.
- **`flowOf(...)`**: 고정된 값 집합으로 Flow를 만듭니다. 예: `flowOf(1, 2, 3)`.
- **`asFlow()`**: 컬렉션·시퀀스·범위 등을 Flow로 변환합니다. 예: `(1..5).asFlow()`.

```kotlin
class NewsRemoteDataSource(
    private val newsApi: NewsApi,
    private val refreshIntervalMs: Long = 5000
) {
    val latestNews: Flow<List<ArticleHeadline>> = flow {
        while (true) {
            val latestNews = newsApi.fetchLatestNews()  // suspend 호출
            emit(latestNews)                             // 값 방출
            delay(refreshIntervalMs)                     // 코루틴 일시 중단
        }
    }
}

interface NewsApi {
    suspend fun fetchLatestNews(): List<ArticleHeadline>
}
```

### flow 빌더의 두 가지 제약 {#flow-builder-constraints}

`flow { }` 빌더는 코루틴 안에서 실행되지만 두 가지 제약을 지켜야 합니다.

1. **순차 실행**: 생산자는 단일 코루틴에서 순서대로 실행됩니다. 위 예시에서 `fetchLatestNews()`가 끝나야 `emit()`이 실행되고, 그 다음 `delay()`로 넘어갑니다. 즉 방출은 항상 순차적입니다.
2. **컨텍스트 보존**: `flow { }` 내부에서는 `withContext`로 코루틴 컨텍스트를 직접 바꿀 수 없습니다. 방출은 반드시 빌더가 호출된 컨텍스트에서 일어나야 하며, 이를 어기면 런타임 예외가 발생합니다. 컨텍스트를 바꾸려면 뒤에서 다룰 `flowOn` 연산자를 쓰고, 다른 컨텍스트에서 값을 방출해야 한다면 `callbackFlow` 같은 다른 빌더를 씁니다.

## 중간 연산자 {#intermediate-operators}

**중간 연산자(intermediate operator)** 는 값을 소비하지 않고 스트림을 변환해, 다시 Flow를 반환합니다. 중요한 성질은 **lazy** 라는 점입니다. 중간 연산자는 선언 시점에 실행되지 않고, 터미널 연산자가 collect를 시작할 때 비로소 동작합니다. 그래서 여러 개를 체이닝해 변환 파이프라인을 구성할 수 있습니다.

```kotlin
val numbers = flowOf(1, 2, 3, 4, 5)

numbers.map { it * 2 }              // 2, 4, 6, 8, 10  — 각 값을 변환
numbers.filter { it % 2 == 0 }      // 2, 4            — 조건에 맞는 값만 통과
numbers.take(3)                     // 1, 2, 3         — 처음 N개만

// transform: 값마다 0개 이상을 방출할 수 있는 일반화된 변환
numbers.transform { value ->
    emit("String: $value")
    emit("Double: ${value * 2}")
}

// distinctUntilChanged: 연속으로 중복되는 값 제거
flowOf(1, 1, 2, 2, 3, 1).distinctUntilChanged()  // 1, 2, 3, 1
```

`map`·`filter`는 값마다 정확히 하나(또는 0개)를 내보내지만, `transform`은 한 입력에 대해 여러 값을 방출할 수 있어 가장 일반적인 변환 연산자입니다.

## 터미널 연산자 {#terminal-operators}

**터미널 연산자(terminal operator)** 는 Flow를 실제로 시작시키는 `suspend` 함수입니다. 터미널 연산자를 호출하기 전까지 중간 연산자는 아무 일도 하지 않습니다.

가장 기본은 `collect` 입니다. 방출되는 모든 값을 순서대로 받습니다.

```kotlin
class LatestNewsViewModel(
    private val newsRepository: NewsRepository
) : ViewModel() {
    init {
        viewModelScope.launch {
            newsRepository.favoriteLatestNews.collect { favoriteNews ->
                updateUi(favoriteNews)
            }
        }
    }
}
```

그 밖의 터미널 연산자도 모두 값을 실제로 수집해 결과를 만들어 냅니다.

```kotlin
val flow = flowOf(1, 2, 3, 4, 5)

flow.first()                            // 1   — 첫 값만 받고 종료
flowOf(42).single()                     // 42  — 값이 정확히 하나여야 함(아니면 예외)
flow.toList()                           // [1, 2, 3, 4, 5]  — 모두 List로 수집
flow.reduce { acc, value -> acc + value } // 15  — 누적해 하나의 값으로 축약
```

## flowOn: 상류 컨텍스트 변경 {#flow-on}

기본적으로 Flow의 생산자는 **collect를 호출한 코루틴의 컨텍스트** 에서 실행됩니다. 하지만 보통 데이터 처리는 백그라운드(IO·Default)에서, UI 갱신은 Main에서 하고 싶습니다.

`flowOn` 연산자는 **자신보다 위쪽(upstream)의 생산자와 중간 연산자의 실행 컨텍스트만** 바꿉니다.

```
생산자 → 연산자1 → 연산자2 → flowOn(IO) → 연산자3 → collect
└──────── IO Dispatcher에서 실행 ────────┘ └─ collect 컨텍스트에서 실행 ─┘
```

- **상류(upstream)**: `flowOn` 이전의 생산자·중간 연산자 → `flowOn`에 지정한 Dispatcher에서 실행됩니다.
- **하류(downstream)**: `flowOn` 이후의 연산자와 `collect` → collect를 호출한 컨텍스트에서 실행됩니다. `flowOn`은 하류에 영향을 주지 않습니다.

`flowOn`을 여러 번 쓰면, 각각 자신의 위치를 기준으로 그 위쪽 컨텍스트를 바꿉니다.

```kotlin
class NewsRemoteDataSource(
    private val newsApi: NewsApi,
    private val ioDispatcher: CoroutineDispatcher
) {
    val latestNews: Flow<List<ArticleHeadline>> = flow {
        val news = newsApi.fetchLatestNews()
        emit(news)
    }.flowOn(ioDispatcher)   // 생산자를 IO Dispatcher로 이동
}

class NewsRepository(
    private val newsRemoteDataSource: NewsRemoteDataSource,
    private val userData: UserData,
    private val defaultDispatcher: CoroutineDispatcher
) {
    val favoriteLatestNews: Flow<List<ArticleHeadline>> =
        newsRemoteDataSource.latestNews
            .map { news -> news.filter { userData.isFavoriteTopic(it) } }  // 상류
            .onEach { news -> saveInCache(news) }                          // 상류
            .flowOn(defaultDispatcher)   // 위 두 연산자를 Default에서 실행
            .catch { emit(lastCachedNews()) }  // 하류 — collect 컨텍스트에서 실행
}
```

실무에서는 위 예시처럼 계층별로 컨텍스트를 나눕니다. 데이터소스의 네트워크·디스크 작업은 `Dispatchers.IO`, Repository의 데이터 가공은 `Dispatchers.Default` 로 각각 `flowOn`을 두고, ViewModel은 메인 컨텍스트에서 수집합니다.

`flow { }` 내부에서 `withContext`로 직접 컨텍스트를 바꾸면 방출 컨텍스트가 어긋나 예외가 발생합니다. Flow에서 컨텍스트 변경은 반드시 `flowOn`으로 해야 합니다.

## callbackFlow: 콜백 API를 Flow로 {#callback-flow}

`callbackFlow`는 **콜백 기반 API(Firebase·위치 서비스 등)를 Flow로 변환** 할 때 쓰는 빌더입니다. 일반 `flow { }`와 달리, 콜백이 다른 스레드·다른 컨텍스트에서 값을 던져도 안전하게 방출할 수 있습니다.

```kotlin
class FirestoreUserEventsDataSource(
    private val firestore: FirebaseFirestore
) {
    fun getUserEvents(): Flow<UserEvents> = callbackFlow {
        // 1. 콜백 리스너 등록
        val subscription = firestore.collection("events")
            .addSnapshotListener { snapshot, _ ->
                if (snapshot == null) return@addSnapshotListener
                // 2. trySend: 코루틴 외부(콜백)에서도 값 방출 가능
                trySend(snapshot.getEvents())
            }

        // 3. Flow가 닫히거나 취소될 때까지 대기하다가 리스너 정리
        awaitClose { subscription.remove() }
    }
}
```

핵심 요소는 두 가지입니다.

- **`trySend` / `send`**: `flow { }`의 `emit`이 `suspend` 함수인 것과 달리, `callbackFlow`는 코루틴 바깥의 콜백에서 호출되는 `send`(suspend)와 `trySend`(non-suspend)를 제공합니다.
- **`awaitClose { }`**: **반드시 호출해야 하는** 마지막 구문입니다. Flow가 수집을 멈추거나 취소될 때까지 빌더를 살려 두었다가, 그 시점에 콜백 리스너를 해제하는 정리 작업을 수행합니다. `awaitClose`가 없으면 빌더 블록이 끝나는 즉시 Flow가 닫혀 콜백 등록이 무의미해지고 리스너 누수가 생깁니다. 그래서 `callbackFlow`는 `awaitClose` 호출이 빠지면 `IllegalStateException` 을 던져 이를 강제합니다.

| 구분 | flow | callbackFlow |
|------|------|--------------|
| 값 방출 함수 | `emit` (suspend) | `send`(suspend) / `trySend`(non-suspend) |
| 외부 컨텍스트 방출 | 불가 (컨텍스트 보존) | 가능 |
| 버퍼링 | 없음 | 있음 (설정 가능) |
| 용도 | 일반 비동기 스트림 | 콜백 기반 API 변환 |

## Cold Flow와 Hot Flow {#cold-vs-hot}

지금까지 다룬 `flow { }` 기반 Flow는 모두 **cold** 입니다. 반면 **StateFlow·SharedFlow는 hot** 입니다. 둘을 가르는 기준은 "값을 보유하는가"가 아니라 **"collector가 없어도 활성화되어 있는가"** 입니다.

- **Cold Flow**: collect하기 전까지 비활성입니다. collect하면 그때 생산자 코드가 실행되고, collector마다 독립적으로 처음부터 다시 실행됩니다.
- **Hot Flow**: collector의 존재와 무관하게 이미 활성화되어 있습니다. 모든 collector가 같은 인스턴스를 공유하며, 같은 방출을 함께 받습니다.

| 구분 | Cold Flow | Hot Flow (StateFlow) |
|------|-----------|----------------------|
| 생성 | `flow { }` | `MutableStateFlow()` |
| 실행 시점 | collect 시 생산자 실행 | 즉시 활성화 |
| 구독자 | collector마다 독립 실행 | 모든 collector가 인스턴스 공유 |
| 초기값 | 없음 | 필수 |
| 용도 | 일회성 작업·네트워크 요청 | UI 상태·실시간 데이터 |

## StateFlow {#state-flow}

`StateFlow`는 **현재 상태를 하나 보유하고 관찰 가능한 Hot Flow** 입니다. 안드로이드 UI 상태 관리에 가장 널리 쓰입니다.

- **항상 최신 값 하나를 보유** 합니다. 새 collector가 구독하면 즉시 현재 값을 전달받습니다.
- **초기값이 필수** 입니다.
- **직전 값과 같으면 방출하지 않습니다**(`equals` 기반 conflation). 동일한 상태가 반복 emit돼도 UI가 불필요하게 갱신되지 않습니다.

```kotlin
class LatestNewsViewModel(
    private val newsRepository: NewsRepository
) : ViewModel() {
    // 외부에는 읽기 전용으로만 노출 (다운캐스팅 방지)
    private val _uiState = MutableStateFlow<LatestNewsUiState>(
        LatestNewsUiState.Success(emptyList())
    )
    val uiState: StateFlow<LatestNewsUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            newsRepository.favoriteLatestNews.collect { favoriteNews ->
                _uiState.value = LatestNewsUiState.Success(favoriteNews)
            }
        }
    }
}

sealed class LatestNewsUiState {
    data class Success(val news: List<ArticleHeadline>) : LatestNewsUiState()
    data class Error(val exception: Throwable) : LatestNewsUiState()
}
```

### stateIn: Flow를 StateFlow로 {#state-in}

`stateIn` 연산자는 **cold Flow를 hot StateFlow로 변환** 합니다. 여러 collector가 하나의 상류 Flow를 공유하도록 만들 때 씁니다.

```kotlin
val latestNews: StateFlow<List<ArticleHeadline>> =
    newsRemoteDataSource.latestNews
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )
```

세 파라미터의 의미는 다음과 같습니다.

- **`scope`**: StateFlow가 활성화될 코루틴 스코프입니다.
- **`started`**: 공유 시작·중지 전략입니다.
  - `Eagerly`: 즉시 시작하고 스코프가 취소될 때까지 유지합니다.
  - `Lazily`: 첫 구독자가 나타나면 시작하고 이후 계속 유지합니다.
  - `WhileSubscribed(timeout)`: 구독자가 있을 때만 활성이고, 마지막 구독자가 사라진 뒤 `timeout`이 지나면 상류를 중지합니다. 화면 회전 같은 짧은 구독 단절에 상류를 불필요하게 재시작하지 않으려고 보통 `5000`ms를 줍니다.
- **`initialValue`**: 상류가 첫 값을 내기 전에 사용할 초기 상태입니다.

## SharedFlow {#shared-flow}

`SharedFlow`는 StateFlow와 같은 Hot Flow지만, **상태를 보유하지 않고 이벤트를 브로드캐스트** 합니다. 토스트·네비게이션처럼 한 번만 처리돼야 하는 일회성 이벤트에 적합합니다.

| 구분 | StateFlow | SharedFlow |
|------|-----------|------------|
| 초기값 | 필수 | 선택적 |
| 현재 값 보유 | 항상 최신 값 유지 | 보유하지 않음 |
| 중복 값 | 같은 값은 무시(conflation) | 모든 값 방출 |
| replay | 1 (최신 값) | 0~N (설정 가능) |
| 용도 | UI 상태 | 일회성 이벤트 |

```kotlin
class NewsViewModel : ViewModel() {
    // UI 상태 — StateFlow
    private val _newsState = MutableStateFlow<NewsState>(NewsState.Loading)
    val newsState: StateFlow<NewsState> = _newsState.asStateFlow()

    // 일회성 이벤트 — SharedFlow
    private val _navigationEvent = MutableSharedFlow<NavigationEvent>()
    val navigationEvent: SharedFlow<NavigationEvent> = _navigationEvent.asSharedFlow()

    fun onArticleClick(articleId: String) {
        viewModelScope.launch {
            _navigationEvent.emit(NavigationEvent.ToArticleDetail(articleId))
        }
    }
}

sealed class NavigationEvent {
    data class ToArticleDetail(val id: String) : NavigationEvent()
}
```

## 안드로이드에서 안전하게 수집하기 {#safe-collection-android}

Hot Flow를 안드로이드에서 그대로 collect하면 위험합니다. `lifecycleScope.launch { collect }`는 Activity가 백그라운드로 가도 수집을 계속하므로, 보이지 않는 화면을 갱신하며 리소스를 낭비하거나 크래시를 유발할 수 있습니다.

```kotlin
// 위험 — Activity가 백그라운드에 있어도 계속 수집
lifecycleScope.launch {
    viewModel.uiState.collect { state -> updateUi(state) }
}
```

### repeatOnLifecycle (View 시스템) {#repeat-on-lifecycle}

`repeatOnLifecycle(Lifecycle.State.STARTED)`는 **지정한 생명주기 상태일 때만 수집** 하고, 그 아래로 내려가면 수집 코루틴을 취소했다가 다시 올라오면 재시작합니다.

```kotlin
class NewsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state -> updateUi(state) }
            }
        }
    }
}
```

### collectAsStateWithLifecycle (Compose) {#collect-as-state-with-lifecycle}

Compose에서는 `collectAsStateWithLifecycle()`이 같은 일을 해 줍니다. Flow를 `State`로 변환하면서, 내부적으로 `repeatOnLifecycle`을 적용해 생명주기를 인식하며 수집합니다. 단순 `collectAsState()`는 생명주기를 인식하지 않으므로, 안드로이드에서는 `collectAsStateWithLifecycle()`을 기본으로 씁니다.

```kotlin
@Composable
fun NewsScreen(viewModel: NewsViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    // uiState 사용 — STARTED 이상일 때만 갱신
}
```

## UI 이벤트: Channel vs SharedFlow {#channel-vs-sharedflow}

ViewModel에서 토스트·네비게이션 같은 일회성 UI 이벤트를 보낼 때 `Channel`과 `SharedFlow` 중 무엇을 쓸지가 자주 논의됩니다. 갈림길은 **"구독자가 없을 때 이벤트가 어떻게 되는가"** 입니다.

```kotlin
// Channel 방식 — 단일 구독자, 전달 보장
class ProfileViewModel : ViewModel() {
    private val _uiEvent = Channel<UiEvent>()
    val uiEvent = _uiEvent.receiveAsFlow()

    fun onSave() = viewModelScope.launch {
        _uiEvent.send(UiEvent.ShowToast("저장 완료"))
    }
}

// SharedFlow 방식 — 다중 구독자, 세밀한 버퍼 제어
class ProfileViewModel2 : ViewModel() {
    private val _uiEvent = MutableSharedFlow<UiEvent>(
        replay = 0,
        extraBufferCapacity = 1,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val uiEvent = _uiEvent.asSharedFlow()
}

sealed class UiEvent {
    data class ShowToast(val message: String) : UiEvent()
    data class ShowError(val message: String?) : UiEvent()
}
```

| 구분 | Channel | SharedFlow |
|------|---------|------------|
| 구독자 수 | 단일 (먼저 받는 쪽이 소비) | 다중 (모두에게 브로드캐스트) |
| 구독자 없을 때 | `send`가 일시 중단되어 보존 (전달 보장) | replay=0이면 손실 |
| 이벤트 소비 | 한 번만 소비 (큐) | 모든 구독자가 받음 |
| 타입 | Flow 아님 (Channel) | Flow |
| 난이도 | 간단 | replay·버퍼 설정 필요 |

기본 `Channel()`은 capacity 0(RENDEZVOUS)이라, collector가 없으면 `send`가 일시 중단되어 이벤트가 보존됩니다. `repeatOnLifecycle`로 화면 회전 중 수집이 잠깐 끊겨도, 재구독 시 그 사이 보낸 이벤트를 받습니다. 그래서 **단일 화면의 일회성 이벤트에는 Channel이 간단하면서도 안전** 합니다.

반면 `SharedFlow(replay=0)`는 구독자가 없을 때 emit하면 이벤트가 손실됩니다. 대신 **여러 구독자에게 동시에 브로드캐스트** 할 수 있고 버퍼 정책을 세밀하게 조절할 수 있습니다. 다만 일회성 이벤트에 `replay=1`을 주면 화면 회전 후 마지막 이벤트가 다시 전달되어 토스트·네비게이션이 중복 처리될 수 있으니 주의해야 합니다.

## 선택 가이드 {#selection-guide}

상황별로 무엇을 쓸지는 다음 기준으로 정리됩니다.

| 요구 | 선택 |
|------|------|
| 단일 값만 필요 | `suspend` 함수 |
| 여러 값을 비동기로 방출 (cold) | `Flow` |
| 현재 상태를 유지·관찰 (UI 상태) | `StateFlow` |
| 일회성 이벤트 · 단일 구독자 | `Channel` |
| 일회성 이벤트 · 다중 구독자 | `SharedFlow` |
| 여러 구독자에게 브로드캐스트 | `SharedFlow` |

## 요약 {#summary}

> **TL;DR** — Flow는 코루틴 위의 비동기 데이터 스트림으로, 기본은 cold라 collect할 때 비로소 생산자가 실행됩니다. `flow`·`flowOf`·`asFlow`로 만들고(순차 실행·컨텍스트 보존 제약), `map`·`filter`·`transform` 같은 중간 연산자로 변환한 뒤 `collect` 같은 터미널 연산자로 수집합니다. 상류 컨텍스트는 `flowOn`으로 바꾸고, 콜백 API는 `callbackFlow`(+`awaitClose`)로 변환합니다. StateFlow·SharedFlow는 hot이며, 각각 UI 상태와 일회성 이벤트에 쓰입니다. 안드로이드에서는 `repeatOnLifecycle`·`collectAsStateWithLifecycle`로 생명주기를 인식하며 수집해야 합니다.

1. **Flow와 cold 특성**: 코루틴 위의 비동기 스트림. cold라 collect 전엔 비활성이고, collector마다 독립 실행된다.
2. **구성 요소**: 생산자(Repository) → 중개자(중간 연산자) → 소비자(ViewModel).
3. **빌더**: `flow`·`flowOf`·`asFlow`. `flow { }`는 순차 실행되고 컨텍스트를 보존한다.
4. **연산자**: 중간 연산자(`map`·`filter`·`transform`)는 lazy하게 변환하고, 터미널 연산자(`collect`·`first`·`toList`·`reduce`)가 스트림을 시작시킨다.
5. **flowOn**: 자신보다 위쪽(상류)의 실행 컨텍스트만 바꾼다. 하류는 collect 컨텍스트 그대로.
6. **callbackFlow**: 콜백 API를 Flow로 변환. `trySend`로 외부에서 방출하고 `awaitClose`로 정리한다.
7. **Cold vs Hot**: 기준은 "collector 없이도 활성인가". StateFlow·SharedFlow가 hot.
8. **StateFlow / stateIn**: 최신 값 하나 보유, conflation. `stateIn`으로 cold Flow를 StateFlow로 변환.
9. **SharedFlow**: 상태 없이 이벤트 브로드캐스트. replay·버퍼 설정 가능.
10. **안전 수집**: View는 `repeatOnLifecycle`, Compose는 `collectAsStateWithLifecycle`.
11. **UI 이벤트**: 단일 구독자·전달 보장이면 Channel, 다중 구독자·버퍼 제어면 SharedFlow.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Flow가 cold라는 말은 무슨 뜻인가요? Hot Flow와는 무엇이 다른가요?">

Cold Flow는 `flow { }` 빌더로 만든 대부분의 Flow처럼, collector가 `collect()`를 호출하기 전까지 아무 동작도 하지 않습니다. collector가 붙는 순간 비로소 생산자 블록이 실행되며, collector마다 독립적으로 스트림이 처음부터 다시 실행됩니다. 그래서 네트워크 요청이나 일회성 데이터 로드처럼 "필요할 때 한 번 흐르는" 작업에 적합합니다.

Hot Flow는 collector의 존재 여부와 무관하게 항상 활성화되어 있고, 모든 collector가 같은 인스턴스를 공유합니다. StateFlow와 SharedFlow가 여기에 속합니다. 둘을 가르는 기준은 "값을 보유하는가"가 아니라 "collector가 없어도 활성화되어 있는가"입니다.

</def>
<def title="Q) flow 빌더의 두 가지 제약(순차 실행, 컨텍스트 보존)은 각각 무엇이고 왜 그런가요?">

첫째는 순차 실행입니다. `flow { }`의 생산자는 단일 코루틴에서 순서대로 실행되므로, `suspend` 호출이 끝나야 다음 `emit`이 일어납니다. 방출은 항상 순차적입니다.

둘째는 컨텍스트 보존입니다. `flow { }` 내부에서는 `withContext`로 컨텍스트를 직접 바꿀 수 없습니다. 방출은 반드시 빌더가 호출된 컨텍스트에서 일어나야 하며, 다른 컨텍스트에서 emit하면 런타임 예외가 납니다. 컨텍스트를 바꾸고 싶다면 `flowOn` 연산자를 써서 상류의 실행 컨텍스트를 옮겨야 하고, 콜백이 다른 스레드에서 값을 던지는 경우라면 `callbackFlow`를 써야 합니다.

</def>
<def title="Q) flowOn 연산자는 어떤 코드의 실행 컨텍스트를 바꾸나요? 상류와 하류를 구분해서 설명해 주시겠어요?">

`flowOn`은 자신을 기준으로 상류(자신보다 위쪽에 선언된 생산자와 중간 연산자)의 실행 컨텍스트만 바꿉니다. `flowOn` 아래쪽의 연산자와 최종 `collect`(하류)는 영향을 받지 않고, collect를 호출한 코루틴의 컨텍스트에서 실행됩니다.

기본적으로 Flow의 생산자는 collect를 호출한 컨텍스트에서 실행되는데, 보통 데이터 처리는 백그라운드(IO·Default)에서 하고 UI 갱신은 Main에서 하고 싶습니다. 이때 무거운 작업이 있는 상류에 `flowOn(Dispatchers.IO)`나 `flowOn(Dispatchers.Default)`를 걸면 생산자만 백그라운드로 옮기고 collect 측은 그대로 Main에 둘 수 있습니다. `flow { }` 안에서 `withContext`로 직접 바꾸면 방출 컨텍스트가 어긋나 예외가 나므로, 컨텍스트 변경은 반드시 `flowOn`으로 합니다.

</def>
<def title="Q) callbackFlow는 언제 쓰고, awaitClose를 빠뜨리면 어떤 문제가 생기나요?">

`callbackFlow`는 Firebase 리스너나 위치 서비스처럼 콜백으로 값을 던지는 API를 Flow로 변환할 때 씁니다. 일반 `flow { }`는 컨텍스트 보존 제약 때문에 다른 스레드의 콜백에서 emit할 수 없지만, `callbackFlow`는 `send`·`trySend`로 코루틴 외부의 콜백에서도 안전하게 값을 방출할 수 있습니다.

`awaitClose { }`는 반드시 호출해야 하는 마지막 구문입니다. Flow가 수집을 멈추거나 취소될 때까지 빌더를 살려 두었다가, 그 시점에 등록한 콜백 리스너를 해제하는 정리 작업을 합니다. `awaitClose`를 빠뜨리면 빌더 블록이 끝나는 즉시 Flow가 닫혀 버려 콜백 등록이 무의미해지고, 리스너가 해제되지 않아 누수가 발생합니다.

</def>
<def title="Q) ViewModel에서 일회성 UI 이벤트를 보낼 때 Channel과 SharedFlow 중 무엇을 고르시겠어요?">

핵심은 "구독자가 없을 때 이벤트가 어떻게 되는가"입니다. 기본 `Channel()`은 capacity 0(RENDEZVOUS)이라 collector가 없으면 `send`가 일시 중단되어 이벤트가 보존됩니다. 전달이 보장되고 한 collector가 정확히 한 번만 소비하며, `repeatOnLifecycle`로 화면 회전 중 수집이 잠깐 끊겨도 재구독 시 그 사이 이벤트를 받습니다. 그래서 단일 화면의 일회성 이벤트에는 Channel이 간단하면서 안전합니다.

`SharedFlow(replay=0)`는 구독자가 없을 때 emit하면 이벤트가 손실됩니다. 대신 여러 구독자에게 동시에 브로드캐스트할 수 있고 `extraBufferCapacity`·`onBufferOverflow`로 버퍼 정책을 제어할 수 있습니다. 그래서 다중 구독자나 세밀한 버퍼 제어가 필요하면 SharedFlow를 씁니다. 다만 일회성 이벤트에 `replay=1`을 주면 화면 회전 후 마지막 이벤트가 재전달되어 중복 처리될 수 있으니 주의합니다.

</def>
<def title="Q) 안드로이드에서 StateFlow를 그냥 lifecycleScope.launch로 수집하면 무엇이 문제이고, 어떻게 고치나요?">

`lifecycleScope.launch { collect }`는 Activity가 백그라운드로 내려가도 수집을 멈추지 않습니다. 보이지 않는 화면을 계속 갱신해 리소스를 낭비하고, 경우에 따라 죽은 뷰를 건드려 크래시로 이어질 수 있습니다.

View 시스템에서는 `repeatOnLifecycle(Lifecycle.State.STARTED) { collect }`로 감싸야 합니다. STARTED 이상일 때만 수집하고, 그 아래로 내려가면 수집 코루틴을 취소했다가 다시 올라오면 재시작합니다. Compose에서는 `collectAsStateWithLifecycle()`을 쓰면 같은 효과를 얻습니다. 내부적으로 `repeatOnLifecycle`을 적용해 생명주기를 인식하며 수집하므로, 생명주기를 모르는 `collectAsState()` 대신 이쪽을 기본으로 써야 합니다.

</def>
</deflist>
