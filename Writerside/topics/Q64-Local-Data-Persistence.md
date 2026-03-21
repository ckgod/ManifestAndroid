# Q64) 로컬 데이터 저장/유지

## 데이터를 로컬에 어떻게 저장하고 유지하나요? {#how-to-store-and-persist-data-locally}

Android는 데이터의 성격에 맞춰 사용할 수 있는 여러 가지 로컬 저장 메커니즘을 제공합니다. 가벼운 키-값 저장이 필요할 때, 구조화된 관계형 데이터를 다룰 때, 파일 형태의 바이너리 데이터를 보관할 때 각각에 적합한 도구가 다릅니다.

### SharedPreferences {#shared-preferences}

[SharedPreferences](https://developer.android.com/training/data-storage/shared-preferences)는 단순한 키-값 저장 메커니즘으로, 앱 설정이나 사용자 환경 설정처럼 가벼운 데이터를 보관하기에 적합합니다. `Boolean`, `Int`, `String`, `Float` 같은 기본 타입을 저장할 수 있고, 앱 재시작 후에도 데이터가 유지됩니다. 다만 동기적으로 동작하기 때문에 메인 스레드를 블로킹할 위험이 있고, DataStore의 등장 이후로 새 프로젝트에서는 점점 덜 선호되는 추세입니다.

```kotlin
val sharedPreferences = context.getSharedPreferences("app_prefs", Context.MODE_PRIVATE)
sharedPreferences.edit {
    putString("user_name", "skydoves")
}
```
{title="SharedPreferencesExample.kt"}

### DataStore {#datastore}

[Jetpack DataStore](https://developer.android.com/topic/libraries/architecture/datastore)는 SharedPreferences를 대체할 수 있도록 만들어진 더 모던하고 확장성 있는 솔루션입니다. 두 가지 형태로 제공되는데, 키-값 저장에는 `PreferencesDataStore`를, 구조화된 데이터에는 `ProtoDataStore`를 사용합니다. SharedPreferences와 달리 비동기로 동작하기 때문에 메인 스레드 블로킹 문제를 피할 수 있습니다.

```kotlin
val dataStore: DataStore<Preferences> = context.createDataStore(name = "settings")

val userNameKey = stringPreferencesKey("user_name")
runBlocking {
    dataStore.edit { settings ->
        settings[userNameKey] = "John Doe"
    }
}
```
{title="DataStoreExample.kt"}

### Room Database {#room}

[Room](https://developer.android.com/training/data-storage/room)은 SQLite 위에 얹어진 고수준 추상화로, 구조화·관계형 데이터를 다루는 데 적합합니다. 어노테이션 기반 정의, 컴파일 시점 검사, LiveData나 Flow를 통한 반응형 프로그래밍 지원 같은 장점을 통해 데이터베이스 관리를 단순화해 줍니다. 복잡한 쿼리가 필요하거나 구조화된 데이터의 양이 많은 앱에 잘 어울립니다.

```kotlin
@Entity
data class User(
    @PrimaryKey val id: Int,
    val name: String
)

@Dao
interface UserDao {
    @Insert
    suspend fun insertUser(user: User)

    @Query("SELECT * FROM User WHERE id = :id")
    suspend fun getUserById(id: Int): User
}

@Database(entities = [User::class], version = 1)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
}
```
{title="RoomDatabaseExample.kt"}

### 파일 저장소 {#file-storage}

바이너리 데이터나 사용자 정의 형식의 데이터는 Android의 내부·외부 저장소에 파일 형태로 저장할 수 있습니다. 내부 저장소는 앱에 비공개이고, 외부 저장소는 다른 앱과 공유할 수 있습니다. 이미지, 비디오, 사용자 정의 직렬화 데이터 같은 자원을 다룰 때 파일 입출력을 사용하는 것이 일반적입니다.

```kotlin
val file = File(context.filesDir, "user_data.txt")
file.writeText("Sample user data")
```
{title="FileStorageExample.kt"}

### 요약 {#summary}

<tldr>
Android에서 어떤 저장 메커니즘을 선택할지는 데이터의 성격과 복잡도에 달려 있습니다. **SharedPreferences** 와 **DataStore** 는 사용자 설정, 기능 플래그처럼 가벼운 키-값 데이터에 적합하고, **Room** 은 구조화된 관계형 데이터를 SQL 기반으로 다루는 데 좋습니다. **파일 저장소** 는 바이너리 파일이나 큰 사용자 정의 데이터셋을 보관하는 데 적합합니다. 각각의 도구가 가진 특성을 이해하고 요구사항에 맞춰 선택하면 효율적이고 안정적인 데이터 보관을 보장할 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 네트워크 API에서 받은 큰 JSON 응답을 오프라인 사용을 위해 로컬에 저장해야 한다면, 어떤 저장 메커니즘을 선택하고 그 이유는 무엇인가요?">

가장 자연스러운 선택은 **Room** 입니다. JSON 자체를 파일로 박아 두는 방식은 단기적으로는 단순해 보이지만, 시간이 지나면서 검색·정렬·페이지네이션 요구가 생기면 결국 데이터 모델을 다시 풀어내야 하는 부담이 따라옵니다. 반면 Room은 JSON을 처음부터 엔티티로 분해해 저장하므로, 오프라인 화면에서 필요한 쿼리를 SQL로 자연스럽게 처리할 수 있고, Flow와 결합하면 데이터 변경에 대해 UI가 반응형으로 갱신됩니다.

Room을 선택할 때의 또 다른 장점은 동기화 흐름과의 조합입니다. 네트워크에서 받은 데이터를 Room에 저장하고 UI는 항상 Room을 기반으로 그리는 단방향 흐름을 만들면, 오프라인 상태와 온라인 상태에서의 동작이 동일해져 버그가 줄어듭니다. 새로 받은 응답이 도착할 때마다 `OnConflictStrategy.REPLACE`로 덮어쓰고, 사용자에게는 단지 "최신 캐시"가 보이도록 하는 형태가 표준적인 패턴입니다.

데이터가 정말 거대한 단일 덩어리이고 분해할 의미가 없는 경우(예: 사용자에게 그대로 다시 던져 줄 큰 미디어 메타데이터 블롭)에는 파일 저장이나 ProtoDataStore도 고려할 수 있습니다. 다만 검색·필터·증분 업데이트 가능성이 조금이라도 있다면 Room으로 시작하는 것이 장기적으로 가장 후회 없는 선택입니다. 키-값 저장인 SharedPreferences/PreferencesDataStore는 큰 JSON 응답을 다루기에는 본래 용도와 맞지 않으니 피하는 것이 좋습니다.

</def>
</deflist>
