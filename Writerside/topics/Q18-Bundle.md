# Q18) Bundle

## `Bundle`의 목적은 무엇인가요? {#Bf2fasdf}
`Bundle`은 `Activity`, `Fragment`, `Service`와 같은 구성 요소 간에 데이터를 전달하는 데 사용되는 키-값 쌍 데이터 구조입니다. 일반적으로 앱 내에서 소량의 데이터를 효율적으로 전송하는 데 사용됩니다. `Bundle`은 가볍고 `Android OS`가 쉽게 관리하고 전송할 수 있는 형식으로 데이터를 직렬화하도록 설계되었습니다.

### `Bundle`의 일반적인 사용 사례 {#Bf211fasdf}

1.  **`Activity` 간 데이터 전달**: 새 `Activity`를 시작할 때, `Intent`에 `Bundle`을 첨부하여 대상 `Activity`로 데이터를 전달할 수 있습니다.
2.  **`Fragment` 간 데이터 전달**: `Fragment` 트랜잭션에서 `Bundle`은 `setArguments()` 및 `getArguments()`와 함께 사용하여 `Fragment` 간에 데이터를 전송합니다.
3.  **인스턴스 상태 저장 및 복원**: `Bundle`은 구성 변경 중에 임시 `UI` 상태를 저장하고 복원하기 위해 `onSaveInstanceState()` 및 `onRestoreInstanceState()`와 같은 `lifecycle methods`에서 사용됩니다.
4.  **`Service`로 데이터 전달**: `Service`를 시작하거나 바인딩된 `Service`로 데이터를 전달할 때 `Bundle`이 데이터를 전달할 수 있습니다.

### `Bundle`의 작동 방식

`Bundle`은 데이터를 키-값 구조로 직렬화하여 작동합니다. 키는 `strings`이며, 값은 `primitive types`, `Serializable`, `Parcelable` 객체 또는 다른 `Bundles`일 수 있습니다. 이를 통해 데이터를 효율적으로 저장하고 전송할 수 있습니다.

### 예시: `Activity` 간 데이터 전달

```kotlin
// Activity A에서 데이터 전송
val intent = Intent(this, ActivityB::class.java).apply {
    putExtra("user_name","John Doe")
    putExtra("user_age", 25)
}
startActivity(intent)

// Activity B에서 데이터 수신
val name = intent.getStringExtra("user_name")
val age = intent.getIntExtra("user_age", -1)
```

이 예시에서 데이터는 `Intent.putExtra()`를 통해 `Bundle` 내부에 패키징됩니다.

### 예시: `Fragment` 간 데이터 전달

```kotlin
// Fragment로 데이터 전송
val fragment = MyFragment().apply {
    arguments = Bundle().apply {
        putString("user_name","Jane Doe")
        putInt("user_age", 30)
    }
}

// Fragment에서 데이터 검색
val name = arguments?.getString("user_name")
val age = arguments?.getInt("user_age")
```

### 예시: 상태 저장 및 복원

```kotlin
override fun onSaveInstanceState(outState: Bundle) {
    super.onSaveInstanceState(outState)
    outState.putString("user_input", editText.text.toString())
}

override fun onRestoreInstanceState(savedInstanceState: Bundle) {
    super.onRestoreInstanceState(savedInstanceState)
    val userInput = savedInstanceState.getString("user_input")
    editText.setText(userInput)
}
```

이 경우 `Bundle`은 화면 회전과 같은 구성 변경 중에도 사용자 입력이 유지되도록 합니다.

### 요약

`Bundle`은 `Android`에서 구성 요소 및 `lifecycle events` 전반에 걸쳐 데이터를 효율적으로 전달하고 보존하는 데 중요한 구성 요소입니다. 가볍고 유연한 구조 덕분에 애플리케이션 상태 및 데이터 전송을 관리하는 데 필수적인 도구입니다.

> Q) `onSaveInstanceState()`는 `Bundle`을 사용하여 구성 변경 중 `UI` 상태를 어떻게 보존하며, `Bundle`에 저장할 수 있는 데이터 유형은 무엇입니까?