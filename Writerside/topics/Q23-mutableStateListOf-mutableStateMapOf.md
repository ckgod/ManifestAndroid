# Q23) mutableStateListOf와 mutableStateMapOf

## mutableStateListOf와 mutableStateMapOf는 무엇인가요? {#what-are-they}

`State` 는 Compose의 snapshot 시스템 위에서 동작하면서, 값이 바뀔 때마다 리컴포지션을 트리거해 UI를 동적으로 갱신하는 핵심 도구입니다. 그런데 `List` 나 `Map` 같은 컬렉션을 다룰 때는 사정이 좀 다릅니다. 표준 변경 메서드는 `State` 에 변화 사실을 알려 주지 않기 때문입니다. 그래서 `mutableStateOf` 안에 들어 있는 가변 컬렉션을 직접 갱신하면 리컴포지션이 일어나지 않고, 컬렉션 안 항목 변화도 추적할 수 없습니다. 다음 예시를 봅시다.

```kotlin
val mutableList by remember { mutableStateOf(mutableListOf("skydoves", "android")) }

LazyColumn {
    item {
        Button(
            onClick = { mutableList.add("kotlin") } // 리컴포지션이 트리거되지 않습니다.
        ) {
            Text(text = "Add")
        }
    }

    items(items = mutableList) { item ->
        Text(text = item)
    }
}
```
{title="MutableStateWithList.kt"}

이 코드에서는 리스트에 항목을 추가해도 Compose가 변화를 인지하지 못해 UI가 기대대로 갱신되지 않습니다. 컬렉션 안의 항목 변화까지 제대로 추적하기 위해 Compose는 `mutableStateListOf` 와 `mutableStateMapOf` 라는 전용 컬렉션을 제공합니다. 이 두 API는 Compose의 snapshot 시스템과 통합되어 있어, 항목이 추가/제거/변경될 때 자동으로 리컴포지션을 트리거해 줍니다.

### mutableStateListOf {#mutable-state-list-of}

`mutableStateListOf` 는 `SnapshotStateList` 를 만듭니다. 일반적인 `MutableList` 처럼 동작하지만 Compose에 최적화되어 있어, 리스트에 가해진 변경이 그 데이터를 사용하는 위치의 리컴포지션만 트리거합니다.

```kotlin
val items = mutableStateListOf("android", "kotlin", "skydoves")
```
{title="MutableStateList.kt"}

리스트에 항목을 추가하거나 제거하면 Compose가 변경을 감지하고 그에 맞춰 상태와 UI를 갱신합니다.

```kotlin
items.add("Jetpack Compose")
items.removeAt(0)
```
{title="MutableStateListExample.kt"}

### mutableStateMapOf {#mutable-state-map-of}

`mutableStateMapOf` 는 `SnapshotStateMap` 을 만듭니다. `MutableMap` 처럼 동작하지만 데이터가 바뀔 때 자동으로 상태와 UI를 갱신해 줍니다.

```kotlin
val userSettings = mutableStateMapOf("theme" to "dark", "notifications" to "enabled")
```
{title="MutableStateMap.kt"}

값을 갱신하면 그 값을 사용하는 UI 요소의 리컴포지션이 트리거됩니다.

```kotlin
userSettings["theme"] = "light"
userSettings.remove("notifications")
```
{title="MutableStateMapExample.kt"}

### 일반적인 사용 패턴 {#common-usages}

`mutableStateListOf` 와 `mutableStateMapOf` 는 Compose에서 반응성을 유지하면서 UI 관련 상태를 보관할 때 흔히 사용됩니다. snapshot 시스템과 통합되어 있어, 변경된 부분에 의존하는 UI 컴포넌트만 리컴포지션 대상이 됩니다.

```kotlin
class UserViewModel : ViewModel() {
    private val mutableUserList = mutableStateListOf("skydoves", "kotlin", "android")
    val userList: StateFlow<List<String>> = MutableStateFlow(mutableUserList) // ViewModel 외부에 안전하게 노출

    fun addUser(user: String) {
        mutableUserList.add(user)
    }

    fun removeUser(user: String) {
        mutableUserList.remove(user)
    }
}

@Composable
fun UserList() {
    val userViewModel = viewModel<UserViewModel>()
    val userList by userViewModel.userList.collectAsStateWithLifecycle()

    // ...
}
```
{title="UserViewModel.kt"}

```kotlin
class SettingsViewModel : ViewModel() {
    private val mutableSettingMap = mutableStateMapOf("theme" to "light", "language" to "English")
    val settings: StateFlow<Map<String, String>> = MutableStateFlow(mutableSettingMap) // 안전한 외부 노출

    fun updateTheme(theme: String) {
        mutableSettingMap["theme"] = theme
    }

    fun removeSetting(key: String) {
        mutableSettingMap.remove(key)
    }
}

@Composable
fun Settings() {
    val settingsViewModel = viewModel<SettingsViewModel>()
    val settings by settingsViewModel.settings.collectAsStateWithLifecycle()

    // ...
}
```
{title="SettingsViewModel.kt"}

### 요약 {#summary}

<tldr>
`mutableStateListOf` 와 `mutableStateMapOf` 는 Compose의 snapshot 시스템과 통합된, 반응형 컬렉션을 제공하는 API입니다. 네트워크 응답이나 데이터베이스 쿼리 결과처럼 도메인 로직에서 흘러온 데이터를 List/Map 형태로 보관하면서 컴포저블이 변화를 자연스럽게 관찰하고 UI를 갱신할 수 있게 만들어 줍니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) mutableStateOf 안에 일반 mutableListOf 를 두면 왜 리컴포지션이 트리거되지 않으며, 어떻게 해결할 수 있나요?">

핵심은 Compose가 **무엇을 관찰하는가** 입니다. `mutableStateOf(mutableListOf(...))` 형태로 만든 State는 그 안에 들어 있는 **List 인스턴스의 참조** 만 추적합니다. `add()` 나 `removeAt()` 같은 메서드는 동일 인스턴스 안에서 내부 데이터만 바꾸기 때문에, State 입장에서는 "참조가 바뀌지 않았다" 고 보고 변화로 인식하지 않습니다. 결과적으로 리컴포지션도 일어나지 않고, 화면에 새 항목이 나타나지 않습니다.

가장 자연스러운 해결책은 `mutableStateListOf` 같은 **snapshot 인지 컬렉션** 을 사용하는 것입니다. `mutableStateListOf` 가 만들어 주는 `SnapshotStateList` 는 내부 변경을 snapshot 시스템에 그대로 알려 주므로, 리스트의 add/remove/replace 가 곧 리컴포지션 트리거가 됩니다. 항목 단위로 변화를 추적하므로 LazyColumn 같은 화면에서 실제로 영향을 받는 항목만 다시 그릴 수 있다는 이점도 있습니다. Map 이라면 `mutableStateMapOf` 가 동일한 역할을 합니다.

또 다른 해결 방향은 **불변 데이터로 모델링하고 매번 새 인스턴스를 발행하는 것** 입니다. 즉 `var items by remember { mutableStateOf(emptyList<String>()) }` 처럼 두고, 수정이 필요할 때 `items = items + "kotlin"` 같이 새 리스트를 할당하는 방식입니다. 이 방식은 ViewModel의 StateFlow나 immutable list 와 자연스럽게 어울리고, 단방향 데이터 흐름을 만들기 좋습니다. 다만 항목이 매우 많거나 변경이 잦은 화면에서는 매번 리스트를 새로 만드는 비용이 부담이 될 수 있어, 그런 경우에는 SnapshotStateList 쪽이 유리합니다.

</def>
<def title="Q) LazyColumn에서 항목을 동적으로 추가/제거할 때 UI 갱신을 효율적으로 추적하려면 어떻게 해야 하나요?">

가장 먼저 손대야 하는 것은 데이터 소스입니다. 동적으로 변할 리스트라면 ViewModel 측에서 `mutableStateListOf` 또는 `StateFlow<ImmutableList<...>>` 형태로 노출하는 것이 일반적입니다. SnapshotStateList 를 그대로 사용하면 항목 단위 변경이 그대로 LazyColumn 으로 전달되고, 항목별 ViewHolder 에 해당하는 영역만 리컴포지션 대상이 됩니다. 또 ImmutableList 기반이라면 stability 가 컴파일러 차원에서 보장되므로, 의존하지 않는 자식 컴포저블의 불필요한 리컴포지션도 함께 줄어듭니다.

그 다음은 **항목의 키와 컨텐트 타입을 명시** 하는 일입니다. `LazyColumn` 의 `items(list, key = { it.id })` 형태로 안정적인 키를 지정해 두면, 항목 추가/제거/이동이 일어났을 때 LazyColumn 이 어떤 항목이 그대로 유지되어야 하는지를 정확히 판단할 수 있습니다. 키가 없거나 인덱스 기반이면 항목 이동 시 다시 그려야 하는 영역이 불필요하게 커지고, 항목이 가진 내부 상태(스크롤, 입력값)도 잘못된 항목에 매칭될 수 있습니다. 다양한 항목 타입을 섞는다면 `contentType = { it::class }` 도 함께 넘겨 주는 편이 LazyColumn 의 재사용 효율을 끌어올립니다.

마지막으로 항목 단위 컴포저블도 stable 하게 유지하는 것이 중요합니다. 항목 데이터 클래스를 `@Immutable` 또는 불변 컬렉션 기반으로 두고, 클릭 콜백처럼 자주 만들어지는 람다는 `remember(item.id)` 로 묶거나 ViewModel 메서드 참조로 끌어올려 같은 인스턴스가 유지되게 합니다. 데이터 소스의 반응성, LazyColumn 의 키, 항목 컴포저블의 stability — 이 세 축을 함께 챙기면 항목 추가/제거가 잦은 화면에서도 매끄러운 UI 갱신과 효율적인 리컴포지션을 동시에 달성할 수 있습니다.

</def>
</deflist>
