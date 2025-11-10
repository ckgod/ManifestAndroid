# E3) Kotlin Delegation

## 위임(Delegation)이란?

위임은 객체가 특정 작업을 다른 객체에게 맡기는 디자인 패턴이다. Kotlin은 언어 차원에서 위임을 지원하며, 두 가지 주요 형태가 있다:

1. **클래스 위임(Class Delegation)**: 인터페이스 구현을 다른 객체에 위임
2. **프로퍼티 위임(Property Delegation)**: 프로퍼티의 getter/setter를 다른 객체에 위임

## 위임 프로퍼티(Delegated Properties) {#delegated-properties}

### 기본 개념

위임 프로퍼티는 `by` 키워드를 사용하여 프로퍼티의 접근 로직을 별도 객체에 위임한다.

```Kotlin
class Example {
    var property: String by Delegate()
}
```

위 코드에서 `property`에 접근할 때:
- 읽기: `Delegate`의 `getValue()` 호출
- 쓰기: `Delegate`의 `setValue()` 호출

### Compose에서의 실제 사용 예

```Kotlin
@Composable
fun SearchResultScreen(
    viewModel: SearchViewModel = hiltViewModel()
) {
    // by 사용: State<T> → T로 자동 언래핑
    val screenState by viewModel.screenState.collectAsState()

    // = 사용: LazyPagingItems<T>를 직접 받음
    val lazyPagingItems = viewModel.searchResultPagingFlow.collectAsLazyPagingItems()

    val lazyListState = rememberLazyListState()
}
```

### by를 사용하는 경우의 동작 방식 {#by-usage}

```Kotlin
val screenState by viewModel.screenState.collectAsState()

// collectAsState()의 반환 타입
fun <T> StateFlow<T>.collectAsState(): State<T>

// State 인터페이스
interface State<out T> {
    val value: T
}

// State는 getValue() 연산자를 가짐
operator fun <T> State<T>.getValue(
    thisObj: Any?,
    property: KProperty<*>
): T = this.value
```

**동작 흐름:**
1. `collectAsState()`는 `State<SearchScreenState>` 객체를 반환
2. `by` 키워드는 위임 객체의 `getValue()` 연산자를 자동으로 호출
3. `screenState`에 접근할 때마다 `State.value`가 자동으로 호출됨
4. 결과: `screenState`의 타입은 `SearchScreenState` (State 래퍼가 벗겨짐)

```Kotlin
// 위임 사용 시
val screenState by viewModel.screenState.collectAsState()
println(screenState)  // SearchScreenState 타입, 직접 사용 가능

// 위임 미사용 시
val screenState = viewModel.screenState.collectAsState()
println(screenState.value)  // State.value로 접근해야 함
```

### by를 사용하지 않는 경우 {#without-by}

```Kotlin
val lazyPagingItems = viewModel.searchResultPagingFlow.collectAsLazyPagingItems()

// collectAsLazyPagingItems()의 반환 타입
fun <T : Any> Flow<PagingData<T>>.collectAsLazyPagingItems(): LazyPagingItems<T>

// LazyPagingItems는 getValue() 연산자가 없음 (위임 불가)
class LazyPagingItems<T : Any> {
    operator fun get(index: Int): T?
    val itemCount: Int
    // getValue() 연산자 없음!
}
```

**왜 by를 사용하지 않는가?**
- `collectAsLazyPagingItems()`는 `LazyPagingItems<T>`를 직접 반환 (State 래퍼 없음)
- `LazyPagingItems`는 `getValue()` 연산자를 제공하지 않음
- 이미 최종 타입이므로 위임이 필요 없음
- `=`로 직접 할당만 하면 됨

### Compose에서 by를 사용하는 패턴

| 함수                                         | 반환 타입             | 사용법 | 실제 타입 |
|--------------------------------------------|-------------------|-----|-------|
| `collectAsState()`                         | `State<T>`        | by  | T     |
| `remember { mutableStateOf(초기값) }`         | `MutableState<T>` | by  | T     |
| `rememberSaveable { mutableStateOf(초기값) }` | `MutableState<T>` | by  | T     |
| `produceState(초기값) { }`                    | `State<T>`        | by  | T     |
| `derivedStateOf { }`                       | `State<T>`        | by  | T     |

**공통점:** 모두 `State<T>` 또는 `MutableState<T>`를 반환하므로 `getValue()` 연산자가 존재

## 표준 라이브러리 위임 프로퍼티

Kotlin 표준 라이브러리는 여러 유용한 위임 프로퍼티를 제공한다.

### lazy (지연 초기화)

프로퍼티가 처음 접근될 때만 초기화된다.

```Kotlin
class DatabaseManager {
    // 비용이 큰 초기화 작업을 지연
    val database: Database by lazy {
        println("데이터베이스 초기화 중...")
        Database.connect("jdbc:postgresql://localhost/mydb")
    }

    fun query() {
        database.execute("SELECT * FROM users")  // 이 시점에 초기화
    }
}

// 사용
val manager = DatabaseManager()
// 아직 데이터베이스 초기화 안 됨
manager.query()  // "데이터베이스 초기화 중..." 출력 후 쿼리 실행
manager.query()  // 초기화 없이 바로 쿼리 실행
```

**lazy의 스레드 모드:**
```Kotlin
// SYNCHRONIZED (기본값): 스레드 안전, 하나의 스레드만 초기화
val prop1 by lazy { /* ... */ }

// PUBLICATION: 여러 스레드가 초기화할 수 있지만, 첫 번째 결과만 사용
val prop2 by lazy(LazyThreadSafetyMode.PUBLICATION) { /* ... */ }

// NONE: 스레드 안전성 없음, 단일 스레드에서만 사용
val prop3 by lazy(LazyThreadSafetyMode.NONE) { /* ... */ }
```

### observable (변경 감지)

프로퍼티 값이 변경될 때마다 콜백이 호출된다.

```Kotlin

class User {
    var name: String by Delegates.observable("초기값") { property, oldValue, newValue ->
        println("${property.name}: $oldValue → $newValue")
    }
}

// 사용
val user = User()
user.name = "Alice"  // 출력: name: 초기값 → Alice
user.name = "Bob"    // 출력: name: Alice → Bob
```

**실전 활용 예:**
```Kotlin
class SettingsViewModel : ViewModel() {
    var isDarkMode: Boolean by Delegates.observable(false) { _, old, new ->
        if (old != new) {
            // 테마 변경 이벤트 발생
            themeManager.applyTheme(if (new) Theme.Dark else Theme.Light)
            analyticsLogger.logThemeChange(new)
        }
    }
}
```

### vetoable (변경 검증)

프로퍼티 값 변경을 조건부로 허용/거부할 수 있다.

```Kotlin
class Account {
    var balance: Int by Delegates.vetoable(0) { _, oldValue, newValue ->
        // 잔액이 음수가 되지 않도록 검증
        newValue >= 0
    }
}

// 사용
val account = Account()
account.balance = 100  // 성공
println(account.balance)  // 100

account.balance = -50  // 거부됨 (false 반환)
println(account.balance)  // 여전히 100
```

**실전 활용 예:**
```Kotlin
class FormViewModel : ViewModel() {
    var age: Int by Delegates.vetoable(0) { _, _, newValue ->
        // 나이는 0~150 사이만 허용
        newValue in 0..150
    }

    var email: String by Delegates.vetoable("") { _, _, newValue ->
        // 이메일 형식 검증
        newValue.matches(Regex("^[A-Za-z0-9+_.-]+@(.+)$"))
    }
}
```

### Map 위임

Map의 키-값을 프로퍼티로 접근할 수 있다.

```Kotlin
class User(map: Map<String, Any?>) {
    val name: String by map
    val age: Int by map
    val email: String by map
}

// 사용
val user = User(mapOf(
    "name" to "Alice",
    "age" to 30,
    "email" to "alice@example.com"
))

println(user.name)   // Alice
println(user.age)    // 30
println(user.email)  // alice@example.com
```

**변경 가능한 Map:**
```Kotlin
class MutableUser(map: MutableMap<String, Any?>) {
    var name: String by map
    var age: Int by map
}

val map = mutableMapOf<String, Any?>()
val user = MutableUser(map)

user.name = "Bob"
user.age = 25

println(map)  // {name=Bob, age=25}
```

**실전 활용 - JSON 파싱:**
```Kotlin
class ApiResponse(json: Map<String, Any?>) {
    val status: String by json
    val message: String by json
    val data: Map<String, Any?>? by json
}
```

## 커스텀 위임 프로퍼티 만들기

### 읽기 전용 프로퍼티

`getValue()` 연산자만 구현하면 된다.

```Kotlin
class LoggingDelegate<T>(private val initialValue: T) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): T {
        println("${property.name} 읽기: $initialValue")
        return initialValue
    }
}

// 사용
class Example {
    val name: String by LoggingDelegate("Kotlin")
}

val example = Example()
println(example.name)
// 출력:
// name 읽기: Kotlin
// Kotlin
```

### 읽기/쓰기 프로퍼티

`getValue()`와 `setValue()` 모두 구현한다.

```Kotlin
class RangeDelegate(private var value: Int, private val range: IntRange) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): Int {
        return value
    }

    operator fun setValue(thisRef: Any?, property: KProperty<*>, newValue: Int) {
        value = when {
            newValue < range.first -> range.first
            newValue > range.last -> range.last
            else -> newValue
        }
        println("${property.name} = $value (범위: $range)")
    }
}

// 사용
class Settings {
    var volume: Int by RangeDelegate(50, 0..100)
    var brightness: Int by RangeDelegate(75, 0..100)
}

val settings = Settings()
settings.volume = 120   // volume = 100 (범위: 0..100)
settings.volume = -10   // volume = 0 (범위: 0..100)
println(settings.volume)  // 0
```

### ReadWriteProperty 인터페이스 사용

```Kotlin
class UpperCaseDelegate : ReadWriteProperty<Any?, String> {
    private var value: String = ""

    override fun getValue(thisRef: Any?, property: KProperty<*>): String {
        return value
    }

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: String) {
        this.value = value.uppercase()
    }
}

// 사용
class User {
    var username: String by UpperCaseDelegate()
}

val user = User()
user.username = "alice"
println(user.username)  // ALICE
```

## 클래스 위임(Class Delegation)

인터페이스 구현을 다른 객체에게 위임할 수 있다.

### 기본 사용법

```Kotlin
interface Repository {
    fun getData(): String
    fun saveData(data: String)
}

class RepositoryImpl : Repository {
    override fun getData(): String = "Data from Repository"
    override fun saveData(data: String) {
        println("Saving: $data")
    }
}

// Repository 인터페이스 구현을 RepositoryImpl 인스턴스에 위임
class ViewModel(repository: Repository) : Repository by repository {
    // Repository의 모든 메서드가 자동으로 위임됨
    // 추가 로직만 구현
    fun processData() {
        val data = getData()  // repository.getData() 호출
        println("Processing: $data")
    }
}

// 사용
val repository = RepositoryImpl()
val viewModel = ViewModel(repository)

viewModel.getData()          // "Data from Repository"
viewModel.saveData("New")    // "Saving: New"
viewModel.processData()      // "Processing: Data from Repository"
```

### 메서드 오버라이드

위임을 사용하면서도 특정 메서드만 오버라이드할 수 있다.

```Kotlin
class CachingViewModel(
    private val repository: Repository
) : Repository by repository {

    private val cache = mutableMapOf<String, String>()

    // getData()만 오버라이드
    override fun getData(): String {
        return cache.getOrPut("data") {
            println("캐시 미스 - Repository에서 가져오기")
            repository.getData()
        }
    }

    // saveData()는 위임된 그대로 사용
}

// 사용
val viewModel = CachingViewModel(RepositoryImpl())
viewModel.getData()  // "캐시 미스 - Repository에서 가져오기" + "Data from Repository"
viewModel.getData()  // 캐시에서 바로 반환, 출력 없음
```

### 실전 활용 - Decorator 패턴

```Kotlin
interface Logger {
    fun log(message: String)
}

class ConsoleLogger : Logger {
    override fun log(message: String) {
        println("[LOG] $message")
    }
}

// 타임스탬프를 추가하는 데코레이터
class TimestampLogger(logger: Logger) : Logger by logger {
    override fun log(message: String) {
        val timestamp = System.currentTimeMillis()
        logger.log("[$timestamp] $message")
    }
}

// 레벨을 추가하는 데코레이터
class LevelLogger(
    private val logger: Logger,
    private val level: String
) : Logger by logger {
    override fun log(message: String) {
        logger.log("[$level] $message")
    }
}

// 사용 - 여러 데코레이터 체이닝
val logger = LevelLogger(
    TimestampLogger(ConsoleLogger()),
    "INFO"
)
logger.log("Application started")
// 출력: [LOG] [INFO] [1234567890] Application started
```

## 실전 활용 패턴

### ViewModel에서 PreferencesDataStore 위임

```Kotlin
class PreferenceDelegate<T>(
    private val dataStore: DataStore<Preferences>,
    private val key: Preferences.Key<T>,
    private val defaultValue: T
) : ReadWriteProperty<Any?, T> {

    private var cachedValue: T? = null

    override fun getValue(thisRef: Any?, property: KProperty<*>): T {
        return cachedValue ?: defaultValue
    }

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {
        cachedValue = value
        CoroutineScope(Dispatchers.IO).launch {
            dataStore.edit { preferences ->
                preferences[key] = value
            }
        }
    }
}

// 사용
class SettingsViewModel(private val dataStore: DataStore<Preferences>) : ViewModel() {
    var isDarkMode: Boolean by PreferenceDelegate(
        dataStore,
        booleanPreferencesKey("dark_mode"),
        false
    )

    var fontSize: Int by PreferenceDelegate(
        dataStore,
        intPreferencesKey("font_size"),
        14
    )
}
```

### Lifecycle-aware 프로퍼티

```Kotlin
class LifecycleAwareDelegate<T>(
    private val lifecycle: Lifecycle,
    private val initialValue: T
) : ReadWriteProperty<Any?, T> {

    private var value: T = initialValue

    override fun getValue(thisRef: Any?, property: KProperty<*>): T {
        if (lifecycle.currentState == Lifecycle.State.DESTROYED) {
            throw IllegalStateException("Cannot access ${property.name} when destroyed")
        }
        return value
    }

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {
        if (lifecycle.currentState == Lifecycle.State.DESTROYED) {
            throw IllegalStateException("Cannot modify ${property.name} when destroyed")
        }
        this.value = value
    }
}

// 사용
class MyFragment : Fragment() {
    private var importantData: String by LifecycleAwareDelegate(
        lifecycle,
        ""
    )
}
```

## 정리

### 위임 프로퍼티를 사용하는 이유

1. **코드 재사용**: 공통 패턴(지연 초기화, 변경 감지 등)을 재사용 가능
2. **관심사 분리**: 프로퍼티 접근 로직과 비즈니스 로직을 분리
3. **보일러플레이트 감소**: getter/setter 코드 반복 제거
4. **타입 안정성**: 컴파일 타임에 타입 체크

### 언제 사용할까?

| 상황 | 추천 방법 |
|------|---------|
| 비용이 큰 초기화를 지연하고 싶을 때 | `lazy` |
| 값 변경을 추적하고 싶을 때 | `observable` |
| 값 변경을 검증하고 싶을 때 | `vetoable` |
| Map을 객체처럼 사용하고 싶을 때 | Map 위임 |
| Compose State를 간편하게 쓰고 싶을 때 | `by` + State |
| 인터페이스 구현을 위임하고 싶을 때 | 클래스 위임 |
| 커스텀 동작이 필요할 때 | 직접 구현 |

### 핵심 요구사항

**프로퍼티 위임:**
- 읽기: `operator fun getValue(thisRef, property): T`
- 쓰기: `operator fun setValue(thisRef, property, value: T)`

**클래스 위임:**
- `class MyClass : Interface by delegateObject`
- 위임 객체가 인터페이스를 구현해야 함

