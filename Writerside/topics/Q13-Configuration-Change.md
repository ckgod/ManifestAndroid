# Q13) 구성 변경

## Q) 12. 구성 변경을 어떻게 처리해야 하나요?

구성 변경을 처리하는 것은 원활한 사용자 경험을 유지하는 데 필수적입니다. 특히 화면 회전, 로케일 변경, 다크 모드와 라이트 모드 간 전환, 글꼴 크기 또는 가중치 조정과 같은 이벤트에서 중요합니다. 
기본적으로 Android 시스템은 이러한 변경이 발생할 때 Activity를 다시 시작하여 일시적인 UI 상태를 잃을 수 있습니다. 이러한 변경을 효과적으로 처리하려면 다음 전략을 고려하십시오

1.  **UI 상태 저장 및 복원**: Activity 재생성 중 UI 상태를 보존하고 복원하기 위해 `onSaveInstanceState()` 및 `onRestoreInstanceState()` 메서드를 구현합니다. 이렇게 하면 구성 변경 후 사용자가 동일한 상태로 돌아갈 수 있습니다.
2.  **Jetpack ViewModel**: 구성 변경에도 유지되는 UI 관련 데이터를 저장하기 위해 `ViewModel` 클래스를 활용합니다. `ViewModel` 객체는 Activity 재생성보다 오래 지속되도록 설계되어 이러한 이벤트 동안 데이터를 관리하는 데 이상적입니다.
3.  **구성 변경 수동 처리**: 애플리케이션이 특정 구성 변경 중에 리소스를 업데이트할 필요가 없고 Activity 재시작을 피하고 싶다면, `AndroidManifest.xml` 파일에서 `android:configChanges` 속성을 사용하여 Activity가 처리할 구성 변경을 선언합니다. 그런 다음 `onConfigurationChanged()` 메서드를 재정의하여 이러한 변경을 수동으로 관리합니다.
4.  **Jetpack Compose에서 `rememberSaveable` 활용**: Jetpack Compose에서는 구성 변경 전반에 걸쳐 UI 상태를 저장하기 위해 `rememberSaveable`을 사용할 수 있습니다. 이는 `onSaveInstanceState()`와 유사하게 작동하지만 Compose에 특화되어 Composable 상태를 일관되게 유지하는 데 도움이 됩니다. 이에 대한 자세한 내용은 *Chapter 1: Jetpack Compose Interview Questions*에서 더 자세히 다룰 것입니다.

## 추가 팁

*   **내비게이션 및 백 스택 보존**: Navigation component를 사용하면 구성 변경 전반에 걸쳐 내비게이션 백 스택이 보존됩니다.
*   **구성 종속 데이터 피하기**: 가능한 경우 구성 종속 값을 UI 레이어에 직접 저장하지 마십시오. 구성 변경 전반에 걸쳐 데이터를 처리하도록 특별히 설계된 `ViewModel`과 같은 대안을 사용하십시오.

## 요약

구성 변경을 적절하게 처리하는 것은 사용자 경험을 향상시키고 예기치 않은 상황으로 인해 사용자 데이터가 보존되고 손실되지 않도록 하는 데 중요합니다. 구성 변경 처리에 대한 포괄적인 가이드는 [공식 Android 문서](https://developer.android.com/guide/topics/resources/runtime-changes)를 참조하십시오.

> 1.  구성 변경을 처리하는 다양한 전략은 무엇이며, 이러한 이벤트 동안 `ViewModel`은 `UI` 관련 데이터를 보존하는 데 어떻게 도움이 됩니까?
> 2.  `AndroidManifest`의 `android:configChanges` 속성은 액티비티 생명주기 동작에 어떤 영향을 미치며, 액티비티 재시작에 의존하는 대신 `onConfigurationChanged()` 메서드를 사용해야 하는 시나리오는 무엇입니까?

#### A) {collapsible="true"}
1. Android는 화면 전환, 언어 변경, 글꼴 크기 조정 등의 구성 변경 시 기본적으로 액티비티를 재생성합니다. 이를 처리하는 주요 전략은 다음과 같습니다.
* `Jetpack ViewModel` 사용: 구성 변경 시에도 생존하는 ViewModel에 UI 데이터를 저장
* `onSaveInstanceState()`: `Bundle에` 간단한 데이터를 저장하여 복원
* `RetainedFragment`: `Fragment의` `retainInstance` 속성 활용 (deprecated)
* `android:configChanges`: 특정 구성 변경 시 액티비티 재생성 방지

`ViewModel`의 데이터 보존 매커니즘: `ViewModel`은 `ViewModelStore`를 통해 관리되며, 구성 변경 시 액티비티가 재생성되어도 `ViewModelStore`는 유지됩니다.
이는 AAC가 제공하는 핵심 기능으로, `ViewModel의` 생명주기가 액티비티/프래그먼트보다 길게 유지되어 데이터를 안전하게 보존할 수 있습니다. 

2. `android:configChanges` 속성의 영향과 사용 시나리오
`android:configChanges` 속성을 설정하면 지정된 구성 변경 발생 시
* 액티비티가 재생성되지 않음 (onDestroy() -> onCreate() 호출 안 됨)
* 대신 `onConfigurationChanged()` 콜백만 호출됨
* 현재 액티비티 인스턴스가 유지되므로 상태 보존 불필요

`onConfigurationChanged()` 사용이 적합한 시나리오
* 비디오 재생: 화면 회전 시 재생 위치를 유지해야 할 때
* WebView 컨텐츠: 웹페이지 스크롤 위치나 폼 데이터 유지
* 카메라 앱 : 프리뷰 세션을 중단 없이 유지
* 게임 애플리케이션: 게임 상태를 잃지 않고 화면 방향 전환
* 네트워크 연결 유지: 진행 중인 다운로드나 소켓 연결 보존

주의사항: Google에선 이 방식을 최후의 수단으로 권장합니다. 리소스 재로딩을 수동으로 처리해야 하며, 다른 구성 변경(언어, 테마 등)은 여전히 액티비티를 재생성시킬 수 있기 때문입니다.