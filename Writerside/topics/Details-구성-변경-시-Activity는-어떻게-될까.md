# Details: 구성 변경 시 Activity는 어떻게 될까?

## 구성 변경 중 Activity에는 어떤 일이 발생할까? {#145DFsdf}

Android에서 구성 변경(예: 화면 회전, 테마 변경, 글꼴 크기 조정 또는 언어 업데이트)이 발생하면 시스템은 새 구성을 적용하기 위해 현재 `Activity`를 소멸하고 다시 생성할 수 있습니다.
이 동작은 앱의 리소스가 업데이트된 구성을 반영하도록 다시 로드되도록 합니다.

### 구성 변경 중 기본 동작

1.  **Activity 소멸 및 재성성**: 구성 변경이 발생하면 `Activity`가 소멸되고 다시 생성됩니다. 이 과정은 다음 단계를 포함합니다.
    *   시스템은 현재 `Activity`의 `onPause()`, `onStop()`, `onDestroy()` 메서드를 호출합니다.
    *   새로운 구성으로 `onCreate()` 메서드를 호출하여 `Activity`가 다시 생성됩니다.
2.  **리소스 다시 로드**: 시스템은 새로운 구성(예: 화면 방향, 테마 또는 로케일)에 따라 `layouts`, `drawables`, `strings`와 같은 리소스를 다시 로드하여 앱이 변경 사항에 적응할 수 있도록 합니다.
3.  **데이터 손실 방지**: 재성성 중 데이터 손실을 방지하기 위해 개발자는 `onSaveInstanceState()` 및 `onRestoreInstanceState()` 메서드를 사용하거나 `ViewModel`을 활용하여 인스턴스 상태를 저장하고 복원할 수 있습니다.

```kotlin
override fun onSaveInstanceState(outState: Bundle) {
    super.onSaveInstanceState(outState)
    outState.putString("user_input", editText.text.toString())
}

override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_main)

    val restoredInput = savedInstanceState?.getString("user_input")
    editText.setText(restoredInput)
}
```

### 재성성을 유발하는 주요 구성 변경 사항

1.  **화면 회전**: 화면의 방향을 세로와 가로로 변경하며, 새로운 크기에 맞춰 `layouts`가 다시 로드됩니다.
2.  **다크/라이트 테마 변경**: 사용자가 다크 모드와 라이트 모드 간에 전환하면 앱은 테마별 리소스(예: 색상 및 스타일)를 다시 로드합니다.
3.  **글꼴 크기 변경**: 장치의 글꼴 크기 설정 조정은 새로운 크기를 반영하기 위해 텍스트 리소스를 다시 로드합니다.
4.  **언어 변경**: 시스템 언어 업데이트는 `localized resources`(예: 다른 언어로 된 `strings`) 로드를 트리거합니다.

### Activity 재성성 피하기

`Activity`를 다시 시작하지 않고 구성 변경을 처리하려면 `manifest` 파일에서 `android:configChanges` 속성을 사용할 수 있습니다.
이 접근 방식은 변경 사항을 프로그래밍 방식으로 처리할 책임을 개발자에게 위임합니다.

```xml
<activity
    android:name=".MainActivity"
    android:configChanges="orientation|screenSize|keyboardHidden"/>
```

이 시나리오에서는 시스템이 `Activity`를 소멸하고 다시 생성하지 않습니다. 대신 `onConfigurationChanged()` 메서드가 호출되어 개발자가 변경 사항을 수동으로 처리할 수 있습니다.

```kotlin
override fun onConfigurationChanged(newConfig: Configuration) {
    super.onConfigurationChanged(newConfig)

    if (newConfig.orientation == Configuration.ORIENTATION_LANDSCAPE) {
        // 가로 모드에 특정한 변경 사항을 처리합니다.
    } else if (newConfig.orientation == Configuration.ORIENTATION_PORTRAIT) {
        // 세로 모드에 특정한 변경 사항을 처리합니다.
    }
}
```

### 요약

구성 변경이 발생하면 기본 동작은 `Activity`를 소멸하고 다시 생성하여 새로운 구성에 적응하기 위해 리소스를 다시 로드하는 것입니다.
개발자는 `onSaveInstanceState()`를 사용하여 `transient UI state`를 보존하거나 `ViewModel`을 사용하여 `non-UI state`를 보존할 수 있습니다. 
재성성을 피하려면 `manifest`에서 `android:configChanges` 속성을 사용하여 변경 사항을 처리할 책임을 개발자에게 위임할 수 있습니다.

> Q) 개발자는 구성 변경으로 인한 `activity recreation` 중 데이터 손실을 어떻게 방지할 수 있으며, `transient` 및 `persistent state`를 처리하는 방법은 무엇입니까?