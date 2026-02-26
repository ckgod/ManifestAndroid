# E2) Kotlin Flow

## Flow란? {#F1}
Flow는 **코루틴 기반의 비동기 데이터 스트림**을 다루는 Kotlin의 타입이다.

### 주요 특징
- **단일 값 vs 여러 값**: suspend 함수는 단일 값만 반환하지만, Flow는 여러 값을 순차적으로 내보낼 수 있다
- **비동기적**: 코루틴 위에서 동작하며, 값을 비동기적으로 생성하고 소비한다
- **논블로킹**: 메인 스레드를 차단하지 않고 네트워크 요청 등의 작업을 안전하게 수행할 수 있다

### Iterator와의 비교
`Iterator`와 유사하게 값들의 순서를 생성하지만, Flow는 suspend 함수를 활용하여 비동기적으로 동작한다는 점이 다르다.

## 데이터 스트림의 구성 요소
Flow 기반 데이터 스트림은 세 가지 주요 엔티티로 구성된다:

* **Producer(생산자)**: 스트림에 데이터를 생성하여 추가한다
    - 코루틴을 활용하여 비동기적으로 데이터를 생성
    - 예: Repository에서 네트워크/DB 데이터를 제공

* **Intermediaries(중개자, 선택적)**: 스트림의 데이터를 변환하거나 필터링한다
    - 중간 연산자(map, filter, transform 등)를 사용
    - 값을 소비하지 않고 가공만 수행

* **Consumer(소비자)**: 최종적으로 스트림의 값을 수집하여 사용한다
    - collect 등의 터미널 연산자를 사용
    - 예: ViewModel에서 UI 상태를 업데이트

![flow.png](flow.png)

### 안드로이드 아키텍처에서의 역할
| 컴포넌트 | 역할 | 예시 |
|---------|------|------|
| Repository | UI 데이터의 생산자 | 네트워크/DB에서 데이터 제공 |
| UI Layer | 사용자 입력 이벤트의 생산자 | 클릭, 텍스트 입력 등 |
| ViewModel | 중개자 + 소비자 | 데이터 변환 및 UI 상태 관리 |

## Flow 생성 {#F1045}

### Flow Builder API
Flow를 생성하는 가장 기본적인 방법은 `flow { }` 빌더를 사용하는 것이다.

```Kotlin
class NewsRemoteDataSource(
    private val newsApi: NewsApi,
    private val refreshIntervalMs: Long = 5000
) {
   val latestNews: Flow<List<ArticleHeadline>> = flow {
       while(true) {
           // 1. 네트워크에서 최신 뉴스 가져오기 (suspend 함수)
           val latestNews = newsApi.fetchLatestNews()

           // 2. 가져온 데이터를 Flow로 방출
           emit(latestNews)

           // 3. 지정된 시간만큼 대기 (코루틴 일시 중단)
           delay(refreshIntervalMs)
       }
   }
}

interface NewsApi {
    suspend fun fetchLatestNews(): List<ArticleHeadline>
}
```

### Flow 빌더의 특성

Flow 빌더는 코루틴 내에서 실행되므로 비동기 API의 이점을 누릴 수 있지만, 다음과 같은 제약사항이 있다:

#### 1. 순차적 실행
- 생산자가 코루틴에서 실행되므로, suspend 함수 호출 시 해당 함수가 완료될 때까지 대기한다
- 위 예제에서 `fetchLatestNews()`가 완료되어야 `emit()`이 실행된다

#### 2. 컨텍스트 변경 제한
- Flow 빌더 내부에서는 `withContext`로 코루틴 컨텍스트를 직접 변경할 수 없다
- 컨텍스트를 변경하려면 `flowOn` 연산자를 사용해야 한다
- 다른 컨텍스트에서 값을 방출해야 한다면 `callbackFlow` 등의 다른 빌더를 사용한다

## 스트림 수정

### 중간 연산자(Intermediate Operators)
중개자는 [중간 연산자](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/)를 사용하여 값을 소비하지 않고 데이터 스트림을 변환할 수 있다.

**중요 특징:**
- 중간 연산자는 즉시 실행되지 않는다 (lazy)
- 터미널 연산자(collect 등)가 호출될 때 비로소 실행된다
- 여러 개를 체이닝하여 복잡한 변환 파이프라인을 구성할 수 있다

### 주요 중간 연산자

```Kotlin
val numbers = flowOf(1, 2, 3, 4, 5)

// map: 각 값을 변환
numbers.map { it * 2 }  // 2, 4, 6, 8, 10

// filter: 조건에 맞는 값만 통과
numbers.filter { it % 2 == 0 }  // 2, 4

// transform: 복잡한 변환 수행 (0개 이상의 값 방출 가능)
numbers.transform { value ->
    emit("String: $value")
    emit("Double: ${value * 2}")
}

// take: 처음 N개만 가져오기
numbers.take(3)  // 1, 2, 3

// distinctUntilChanged: 연속된 중복 값 제거
flowOf(1, 1, 2, 2, 3, 1).distinctUntilChanged()  // 1, 2, 3, 1
``` 

## Flow에서 데이터 수집 {#F14}

### 터미널 연산자(Terminal Operators)
Flow에서 실제로 값을 수집하려면 **터미널 연산자**를 사용해야 한다. 터미널 연산자는 Flow를 실제로 시작시키는 suspend 함수다.

### collect
가장 기본적인 터미널 연산자로, 스트림에서 방출되는 모든 값을 수집한다.

```Kotlin
class LatestNewsViewModel(
    private val newsRepository: NewsRepository
) : ViewModel() {

    init {
        viewModelScope.launch {
            // Flow에서 값을 수집하여 처리
            newsRepository.favoriteLatestNews.collect { favoriteNews ->
                // UI에 최신 뉴스 업데이트
                updateUi(favoriteNews)
            }
        }
    }
}
```

### 기타 유용한 터미널 연산자

```Kotlin
val flow = flowOf(1, 2, 3, 4, 5)

// first(): 첫 번째 값만 가져오기
val first = flow.first()  // 1

// single(): 단일 값 가져오기 (여러 값이 있으면 예외)
val single = flowOf(42).single()  // 42

// toList(): 모든 값을 List로 수집
val list = flow.toList()  // [1, 2, 3, 4, 5]

// reduce(): 값들을 누적하여 하나의 값으로 축약
val sum = flow.reduce { acc, value -> acc + value }  // 15
```

## 다른 코루틴 컨텍스트에서 실행

### flowOn 연산자 개요
기본적으로 Flow의 생산자는 `collect`를 호출하는 코루틴의 컨텍스트에서 실행된다. 하지만 Repository의 데이터 처리는 IO 스레드에서, UI 업데이트는 Main 스레드에서 실행하는 것이 일반적이다.

`flowOn` 연산자를 사용하면 Flow의 코루틴 컨텍스트를 변경할 수 있다.

### 동작 방식

```
Producer → Operator1 → Operator2 → flowOn(IO) → Operator3 → Collector
     ←──────────── IO Dispatcher ──────────→   ← Collector's Context →
```

**중요:**
- **Upstream(업스트림)**: `flowOn` 이전의 생산자와 중간 연산자 → 지정된 Dispatcher에서 실행
- **Downstream(다운스트림)**: `flowOn` 이후의 중간 연산자와 소비자 → collect하는 컨텍스트에서 실행
- 여러 개의 `flowOn`을 사용하면, 각각 자신의 위치에서 업스트림 컨텍스트를 변경한다

### 사용 예제

```Kotlin
class NewsRepository(
    private val newsRemoteDataSource: NewsRemoteDataSource,
    private val userData: UserData,
    private val defaultDispatcher: CoroutineDispatcher
) {
    val favoriteLatestNews: Flow<List<ArticleHeadline>> =
        newsRemoteDataSource.latestNews
            // ─── Upstream (defaultDispatcher에서 실행) ───
            .map { news ->
                // 사용자가 즐겨찾는 주제로 필터링
                news.filter { userData.isFavoriteTopic(it) }
            }
            .onEach { news ->
                // 캐시에 저장
                saveInCache(news)
            }
            // flowOn 기준으로 위/아래가 나뉨
            .flowOn(defaultDispatcher)
            // ─── Downstream (collect하는 컨텍스트에서 실행) ───
            .catch { exception ->
                // 에러 발생 시 캐시된 데이터 제공
                emit(lastCachedNews())
            }
}
```

```Kotlin
class NewsRemoteDataSource(
    private val newsApi: NewsApi,
    private val ioDispatcher: CoroutineDispatcher
) {
    val latestNews: Flow<List<ArticleHeadline>> = flow {
        // 네트워크 요청 - IO Dispatcher에서 실행됨
        val news = newsApi.fetchLatestNews()
        emit(news)
    }.flowOn(ioDispatcher)  // Flow 생산자를 IO Dispatcher로 이동
}
```

**베스트 프랙티스:**
- **DataSource 레이어**: I/O 작업 → `Dispatchers.IO` 사용
- **Repository 레이어**: 데이터 가공 → `Dispatchers.Default` 사용
- **ViewModel 레이어**: UI 업데이트 → `Dispatchers.Main`에서 collect

## 콜백 기반 API를 Flow로 변환

### callbackFlow
콜백 기반 API(Firebase, 위치 서비스 등)를 Flow로 변환할 때 사용하는 Flow 빌더다.

```Kotlin
class FirestoreUserEventsDataSource(
    private val firestore: FirebaseFirestore
) {
    // Firestore database에서 user events를 가져오는 함수
    fun getUserEvents(): Flow<UserEvents> = callbackFlow {

        // 1. Firestore 컬렉션 레퍼런스 가져오기
        var eventsCollection: CollectionReference? = null
        try {
            eventsCollection = FirebaseFirestore.getInstance()
                .collection("collection")
                .document("app")
        } catch (e: Throwable) {
            // Firebase 초기화 실패 시 스트림 닫기
            close(e)
        }

        // 2. Firestore에 콜백 리스너 등록
        val subscription = eventsCollection?.addSnapshotListener { snapshot, _ ->
            if (snapshot == null) { return@addSnapshotListener }

            // 3. 새로운 이벤트를 Flow로 전송
            // trySend: 코루틴 외부에서도 값을 방출 가능
            try {
                trySend(snapshot.getEvents()).isSuccess
            } catch (e: Throwable) {
                // 에러 처리
            }
        }

        // 4. Flow가 취소되면 리스너 제거
        // awaitClose: Flow가 닫힐 때까지 대기하다가 정리 작업 수행
        awaitClose { subscription?.remove() }
    }
}
```

### callbackFlow vs flow

| 특징      | flow                    | callbackFlow         |
|---------|-------------------------|----------------------|
| 컨텍스트 변경 | 불가능 (withContext 사용 불가) | 가능                   |
| 값 방출 함수 | emit (suspend 함수)       | send/trySend (일반 함수) |
| 사용 사례   | 일반적인 비동기 작업             | 콜백 기반 API 변환         |
| 버퍼링     | 없음                      | 있음 (설정 가능)           |

## StateFlow와 SharedFlow

### StateFlow 개요 {#SF1}
`StateFlow`는 **Hot Flow**의 한 종류로, **현재 상태를 유지하고 관찰 가능한 Flow**다.

**주요 특징:**
- 항상 **최신 값을 하나 보유**하고 있다
- 새로운 collector가 구독하면 즉시 **현재 값을 전달**받는다
- **동일한 값은 방출하지 않는다** (값이 실제로 변경되었을 때만 방출)
- Android에서 UI 상태 관리에 이상적이다

### Cold Flow vs Hot Flow 비교

#### Cold Flow
* `flow { ... }` 빌더로 만든 대부분의 Flow
* `collect()`가 호출되기 전까지는 아무것도 하지 않음.
* `collect()`가 호출되면, 그때서야 Flow가 활성화되어 값을 생성하고 방출함.

#### Hot Flow
* StateFlow와 SharedFlow가 여기 속함.
* `collect()`하는 대상이 있든 없든, Flow 자체가 이미 활성화되어 있음.
* 값을 생성하거나 이벤트를 받을 준비가 항상 되어있음.

| 구분 | Cold Flow | Hot Flow (StateFlow) |
|------|-----------|----------------------|
| 생성 방식 | flow { } | MutableStateFlow() |
| 실행 시점 | collect 시 생산자 코드 실행 | 즉시 활성화 |
| 구독자 수 | 각 collector마다 독립적 실행 | 모든 collector가 같은 인스턴스 공유 |
| 초기값 | 없음 | 필수 |
| 사용 사례 | 일회성 작업, 네트워크 요청 | UI 상태, 실시간 데이터 |

Hot Flow의 기준은 "값을 보유하는가"가 아니라, "Collector(수집가)가 없어도 활성화되어 있는가"이다.

### StateFlow 사용 예제

```Kotlin
class LatestNewsViewModel(
    private val newsRepository: NewsRepository
) : ViewModel() {
    // private 변경 가능한 StateFlow
    private val _uiState = MutableStateFlow<LatestNewsUiState>(
        LatestNewsUiState.Success(emptyList())
    )

    // public 읽기 전용 StateFlow (다운캐스팅 방지)
    val uiState: StateFlow<LatestNewsUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            newsRepository.favoriteLatestNews
                .collect { favoriteNews ->
                    // UI 상태 업데이트
                    _uiState.value = LatestNewsUiState.Success(favoriteNews)
                }
        }
    }
}

sealed class LatestNewsUiState {
    data class Success(val news: List<ArticleHeadline>): LatestNewsUiState()
    data class Error(val exception: Throwable): LatestNewsUiState()
}
```

### Android에서 안전하게 collect하기

**잘못된 방법:**
```Kotlin
class NewsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 위험: Activity가 백그라운드에 있어도 계속 수집함
        lifecycleScope.launch {
            viewModel.uiState.collect { state ->
                updateUi(state)  // 크래시 가능!
            }
        }
    }
}
```

**올바른 방법:**
```Kotlin
class NewsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // repeatOnLifecycle: STARTED 상태일 때만 수집
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    updateUi(state)  // 안전!
                }
            }
        }
    }
}
```

### Flow를 StateFlow로 변환: stateIn

```Kotlin
class NewsRepository(
    private val newsRemoteDataSource: NewsRemoteDataSource
) {
    // Cold Flow를 Hot StateFlow로 변환
    val latestNews: StateFlow<List<ArticleHeadline>> =
        newsRemoteDataSource.latestNews
            .stateIn(
                scope = CoroutineScope(Dispatchers.Default),
                started = SharingStarted.WhileSubscribed(5000),
                initialValue = emptyList()
            )
}
```

**stateIn 파라미터:**
- `scope`: StateFlow가 활성화될 코루틴 스코프
- `started`: 구독 시작/중지 전략
    - `Eagerly`: 즉시 시작, 스코프가 취소될 때까지 유지
    - `Lazily`: 첫 구독자가 나타나면 시작, 영구 유지
    - `WhileSubscribed(timeout)`: 구독자가 있을 때만 활성, timeout 후 중지
- `initialValue`: 초기 상태 값

### SharedFlow란?
`SharedFlow`는 StateFlow와 유사한 Hot Flow지만, **상태를 보유하지 않고 이벤트를 브로드캐스트**한다.

**StateFlow vs SharedFlow:**

| 특징 | StateFlow | SharedFlow |
|------|----------|---------|
| 초기값 | 필수 | 선택적 |
| 현재 값 보유 | 항상 최신 값 유지 | 값 보유하지 않음 |
| 중복 값 방출 | 동일한 값 무시 | 모든 값 방출 |
| Replay | 1 (최신 값만) | 0~N (설정 가능) |
| 사용 사례 | UI 상태 | 일회성 이벤트 (토스트, 네비게이션) |

```Kotlin
class NewsViewModel : ViewModel() {
    // StateFlow: UI 상태
    private val _newsState = MutableStateFlow<NewsState>(NewsState.Loading)
    val newsState: StateFlow<NewsState> = _newsState.asStateFlow()

    // SharedFlow: 일회성 이벤트
    private val _navigationEvent = MutableSharedFlow<NavigationEvent>()
    val navigationEvent: SharedFlow<NavigationEvent> = _navigationEvent.asSharedFlow()

    fun onArticleClick(articleId: String) {
        viewModelScope.launch {
            // 네비게이션 이벤트 발생 (한 번만 처리되어야 함)
            _navigationEvent.emit(NavigationEvent.ToArticleDetail(articleId))
        }
    }
}

sealed class NavigationEvent {
    data class ToArticleDetail(val id: String) : NavigationEvent()
}
```

### UI 이벤트: Channel vs SharedFlow

ViewModel에서 일회성 UI 이벤트(토스트, 네비게이션, 스낵바 등)를 처리할 때 `Channel`과 `SharedFlow` 중 어떤 것을 사용해야 할까?

#### Channel 방식 {#channel-approach}

```Kotlin
class NewsViewModel : ViewModel() {
    private val _uiEvent = Channel<UiEvent>()
    val uiEvent = _uiEvent.receiveAsFlow()

    fun onSaveClick() {
        viewModelScope.launch {
            try {
                saveNews()
                _uiEvent.send(UiEvent.ShowToast("저장 완료"))
            } catch (e: Exception) {
                _uiEvent.send(UiEvent.ShowError(e.message))
            }
        }
    }
}

// UI에서 수집
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiEvent.collect { event ->
            when (event) {
                is UiEvent.ShowToast -> showToast(event.message)
                is UiEvent.ShowError -> showError(event.message)
            }
        }
    }
}
```

#### SharedFlow 방식 {#sharedflow-approach}

```Kotlin
class NewsViewModel : ViewModel() {
    private val _uiEvent = MutableSharedFlow<UiEvent>()
    val uiEvent = _uiEvent.asSharedFlow()

    fun onSaveClick() {
        viewModelScope.launch {
            try {
                saveNews()
                _uiEvent.emit(UiEvent.ShowToast("저장 완료"))
            } catch (e: Exception) {
                _uiEvent.emit(UiEvent.ShowError(e.message))
            }
        }
    }
}

// UI에서 수집 (동일한 방식)
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiEvent.collect { event ->
            when (event) {
                is UiEvent.ShowToast -> showToast(event.message)
                is UiEvent.ShowError -> showError(event.message)
            }
        }
    }
}
```

#### Channel vs SharedFlow 비교 {#channel-vs-sharedflow}

| 특징 | Channel | SharedFlow |
|------|---------|-----------|
| 구독자 수 | 단일 구독자 (먼저 수집하는 쪽이 소비) | 여러 구독자 가능 (모두에게 브로드캐스트) |
| 이벤트 손실 | 구독 전 이벤트 손실 가능 | 구독 전 이벤트 손실 가능 (replay=0) |
| 이벤트 소비 | 한 번만 소비됨 (큐 방식) | 모든 구독자가 받음 (브로드캐스트) |
| 버퍼 전략 | 다양한 버퍼 전략 지원 | extraBufferCapacity로 설정 |
| 타입 | Flow가 아님 (Channel) | Flow 타입 |
| 사용 난이도 | 간단 | 약간 복잡 (replay, extraBufferCapacity 설정 필요) |

#### 어떤 것을 사용해야 할까? {#which-to-use}

**Channel을 사용하는 경우:**
```Kotlin
// 단일 화면에서만 이벤트를 처리하는 경우
class ProfileViewModel : ViewModel() {
    private val _events = Channel<ProfileEvent>()
    val events = _events.receiveAsFlow()

    // 장점: 간단하고 직관적
    // 단점: 화면 회전 시 이벤트 손실 가능
}
```

**SharedFlow를 사용하는 경우:**
```Kotlin
// 여러 구독자가 있거나 더 세밀한 제어가 필요한 경우
class ProfileViewModel : ViewModel() {
    private val _events = MutableSharedFlow<ProfileEvent>(
        replay = 0,              // 새 구독자에게 재방출하지 않음
        extraBufferCapacity = 1, // 구독자가 없어도 1개 이벤트 버퍼링
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val events = _events.asSharedFlow()

    // 장점: 여러 구독자 지원, 세밀한 제어 가능
    // 단점: 설정이 복잡함
}
```

#### 권장 사항 {#recommendations}

| 시나리오 | 권장 방식 | 이유 |
|---------|---------|-----|
| 단일 Activity/Fragment | Channel | 간단하고 충분함 |
| 여러 구독자 필요 | SharedFlow | 브로드캐스트 지원 |
| 화면 회전 시 이벤트 보존 | SharedFlow (replay=1) | 최근 이벤트 재전달 |
| 간단한 일회성 이벤트 | Channel | 코드가 더 간결함 |

**일반적인 베스트 프랙티스:**
- **간단한 경우**: Channel 사용 (대부분의 경우)
- **복잡한 요구사항**: SharedFlow 사용 (여러 구독자, 이벤트 버퍼링 등)

```Kotlin
sealed class UiEvent {
    data class ShowToast(val message: String) : UiEvent()
    data class ShowError(val message: String?) : UiEvent()
    data class Navigate(val route: String) : UiEvent()
}
```

## 정리

### 선택 가이드 {#selection-guide}

**어떤 방식을 사용해야 할까?**

```
단일 값만 필요한가?
    ↓ YES
suspend 함수 사용

    ↓ NO
여러 값을 비동기로 방출해야 하는가?
    ↓ YES

현재 상태를 유지해야 하는가?
    ↓ YES → StateFlow 사용 (UI 상태)
    ↓ NO

일회성 UI 이벤트인가?
    ↓ YES
    여러 구독자가 필요한가?
        ↓ YES → SharedFlow 사용
        ↓ NO  → Channel 사용 (더 간단)

    ↓ NO
여러 구독자에게 브로드캐스트해야 하는가?
    ↓ YES → SharedFlow 사용
    ↓ NO  → Flow 사용 (일반 스트림)
```

### 핵심 개념 요약

1. **Flow 생성**: `flow { emit() }` 빌더 사용
2. **중간 연산자**: map, filter, transform 등으로 데이터 변환
3. **터미널 연산자**: collect, first, toList 등으로 값 수집
4. **컨텍스트 변경**: flowOn으로 업스트림 Dispatcher 변경
5. **콜백 변환**: callbackFlow로 콜백 기반 API를 Flow로 변환
6. **상태 관리**: StateFlow로 UI 상태 관리
7. **일회성 이벤트**:
   - 단일 구독자 → Channel 사용
   - 여러 구독자 → SharedFlow 사용
8. **안전한 수집**: repeatOnLifecycle로 생명주기 인식 수집