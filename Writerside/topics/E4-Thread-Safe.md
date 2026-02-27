# E4) Thread Safe

## Thread Safe 하다는 것은 어떤 의미인가요?

Thread Safe란 여러 스레드가 동시에 같은 자원(변수, 객체, 데이터 구조 등)에 접근할 때, **실행 순서와 무관하게 항상 올바른 결과를 보장**하는 성질을 말합니다.

핵심 문제는 **Race Condition**입니다. 두 스레드가 동시에 같은 데이터를 읽고 쓸 때 예측 불가능한 결과가 발생하는 것입니다.

```Kotlin
// Race Condition 예시
var count = 0

// Thread A: count++ → 내부적으로 read(0) → +1 → write(1)
// Thread B: count++ → 내부적으로 read(0) → +1 → write(1)
// 결과: 2가 되어야 하지만 1이 될 수 있음
```

### Thread Safety를 보장하는 주요 매커니즘

#### `synchronized` / `@GuardedBy`

```Kotlin
class Counter {
    private var count = 0
    
    @Synchronized
    fun increment() {
        count++ // 한 번에 하나의 스레드만 진입
    }
}
```

`synchronized`는 **모니터 락(monitor lock)**을 사용합니다. 
한 스레드가 락을 획득하면 다른 스레드는 대기합니다.

#### `volatile`

```Kotlin
@Volatile var isRunning = true
```

`volatile`은 JMM에서 <tooltip term="Happens_Before">happens-before</tooltip> 관계를 보장합니다. 쓰기 후 읽기가 항상 최신 값을 보도록 강제합니다.
단, **복합 연산(read-modifiy-write)**은 atomic하지 않으므로 `volatile`만으로는 Race Condition을 완전히 막을 수 없습니다.

#### `AtomicInteger` / `AtomicReference`

```Kotlin
val count = AtomicInteger(0)
count.incrementAndGet() // CAS(Compare-And-Swap) 연산으로 atomic 보장
```

**CAS(Compare-And-Swap)** 는 CPU 명령어 수준의 원자 연산입니다. `synchronized`보다 Lock 없이 동작하므로 성능이 좋습니다.

### 안드로이드에서 Thread Safety가 필요한 상황 {#thread-safe-in-android}

#### ViewModel + StateFlow

```Kotlin
class MyViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState

    fun loadData() {
        viewModelScope.launch(Dispatchers.IO) {  // IO 스레드
            val result = repository.fetch()
            _uiState.value = UiState(data = result)  // StateFlow는 Thread Safe
        }
    }
}
```

`StateFlow`는 내부적으로 `AtomicReference`를 사용하여 Thread Safe 합니다.

> [Kotlin StateFlow 소스코드](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-core/common/src/flow/StateFlow.kt) → `compareAndSet` 메서드 기반

#### Room Database

Room은 기본적으로 **메인 스레드에서의 쿼리를 금지**합니다. (`IllegalStateException`).

Coroutine `suspend` 함수나 `Flow`를 사용하면 Room이 내부적으로 스레드를 관리합니다.

```Kotlin
@Dao
interface UserDao {
    @Query("SELECT * FROM users")
    fun getUsers(): Flow<List<User>>  // Room이 백그라운드에서 자동 처리
}
```

#### SharedPreferences vs DataStore

`SharedPreferences.apply()`는 비동기이지만 Thread Safe하지 않은 케이스가 있어, Android 팀은 DataStore를 공식 대안으로 제시했습니다.

```Kotlin
// DataStore는 Coroutine + Flow 기반으로 Thread Safe 보장
val Context.dataStore: DataStore<Preferences> by preferencesDataStore("settings")

suspend fun saveToken(token: String) {
    context.dataStore.edit { prefs ->
        prefs[TOKEN_KEY] = token
    }
}
```

#### Singleton 패턴 (e.g., Repository, NetworkClient)

```Kotlin
// Double-Checked Locking — volatile 없으면 Thread Unsafe
class Repository private constructor() {
    companion object {
        @Volatile
        private var instance: Repository? = null

        fun getInstance(): Repository =
            instance ?: synchronized(this) {
                instance ?: Repository().also { instance = it }
            }
    }
}
```

`@Volatile` 없이 Double-Checked Locking을 구현하면 **JVM의 명령어 재정렬(instruction reordering)** 때문에 초기화되지 않은 객체가 반환될 수 있습니다.