# Android Manifest Notes

이 문서는 [skydoves/manifest-android-interview](https://github.com/skydoves/manifest-android-interview) 내용을 기반으로 안드로이드 핵심 CS 지식을 학습하고 정리한 프로젝트입니다.

## 학습 목차

### 1.1 Android Framework

Android 플랫폼의 기본 구조와 핵심 개념들을 다룹니다.

- [Q1. Android란?](Q1-Android.md) - Android 운영체제의 기본 개념과 아키텍처
- [Q2. Intent](Q2-Intent.md) - 컴포넌트 간 통신을 위한 Intent 시스템
- [Q3. PendingIntent](Q3-Pending-Intent.md) - 지연 실행을 위한 PendingIntent
- [Q4. Serializable & Parcelable](Q4-Serializable-Parcelable.md) - 객체 직렬화 방법들
  - [Details: Parcel and Parcelable](Details-Parcel-and-Parcelable.md)
- [Q5. Context](Q5-Context.md) - Android의 Context 개념과 올바른 사용법
  - [Details: 올바른 Context 사용법](Details-올바른-Context-사용법.md)
  - [Details: ContextWrapper](Details-ContextWrapper.md)
  - [Details: This vs BaseContext](Details-This-vs-BaseContext.md)
- [Q6. Application Class](Q6-Application-Class.md) - Application 클래스의 역할과 활용
- [Q7. AndroidManifest](Q7-AndroidManifest.md) - 앱 구성 정보를 담는 매니페스트 파일
- [Q8. Activity Lifecycle](Q8-Activity-LifeCycle.md) - 액티비티 생명주기 관리
  - [Details: Lifecycle 인스턴스란](Details-Lifecycle-인스턴스란.md)
  - [Details: 여러 Activity 간 수명 주기 변화](Details-여러-Activity-간-수명-주기-변화.md)
- [Q9. Fragment 생명주기](Q9-Fragment-생명주기.md) - 프래그먼트 생명주기와 관리
  - [Details: Fragment의 viewLifecycleOwner 인스턴스](Details-Fragment의-viewLifecycleOwner-인스턴스.md)
  - [Details: fragmentManager와 childFragmentManager의 차이점](Details-fragmentManager와-childFragmentManager의-차이점.md)
- [Q10. Service](Q10-Service.md) - 백그라운드 작업을 위한 Service 컴포넌트
  - [Details: Service의 생명주기](Details-Service의-생명주기.md)
  - [Details: Forground Service](Details-Forground-Service.md)
- [Q11. BroadcastReceiver](Q11-BroadcastReceiver.md) - 시스템 및 앱 이벤트 수신
- [Q12. ContentProvider](Q12-ContentProvider.md) - 앱 간 데이터 공유를 위한 ContentProvider
  - [Details: 앱 시작 시 ContentProvider 사용하여 구성을 초기화하기](Details-앱-시작-시-ContentProvider-사용하여-구성을-초기화하기.md)
- [Q13. Configuration Change](Q13-Configuration-Change.md) - 구성 변경 처리 전략
  - [Details: 구성 변경 시 Activity는 어떻게 될까](Details-구성-변경-시-Activity는-어떻게-될까.md)
- [Q14. Memory Management](Q14-Memory-Management.md) - Android 메모리 관리 및 최적화
- [Q15. ANR](Q15-ANR.md) - Application Not Responding 문제 이해와 해결
- [Q16. Deep Link](Q16-Deep-Link.md) - 딥링크를 통한 앱 진입점 구성
- [Q17. Task와 Back Stack](Q17-Task와-back-stack.md) - Task 및 백스택 관리
- [Q18. Bundle](Q18-Bundle.md) - 데이터 전달을 위한 Bundle 활용
- [Q19. Activity Fragment 데이터 전달](Q19-Activity-Fragment-데이터-전달.md) - 컴포넌트 간 데이터 전달 방법
  - [Details: Fragment Result API](Details-Fragment-Result-API.md)
- [Q20. ActivityManager](Q20-ActivityManager.md) - ActivityManager의 역할과 활용
- [Q21. SparseArray](Q21-SparseArray.md) - 메모리 효율적인 데이터 구조
- [Q22. 런타임 권한](Q22-Runtime-Permission.md) - 런타임 권한 요청 및 처리
- [Q23. Looper, Handler, HandlerThread](Q23-Looper-Handler-HandlerThread.md) - 스레드 간 통신 메커니즘
- [Q24. Exception Tracing](Q24-Exception-Tracing.md) - 예외 추적 및 디버깅 방법
- [Q25. Build Variants, Flavors](Q25-Build-Variants-Flavors.md) - 빌드 변형 및 Flavor 관리
- [Q26. 접근성](Q26-Accessibility.md) - 접근성 구현 및 보장
- [Q27. File System](Q27-File-System.md) - Android 파일 시스템과 저장소 관리
- [Q28. ART, Dalvik, Dex, Compiler](Q28-ART-Dalvik-Dex-Compiler.md) - Android 런타임과 컴파일 시스템
- [Q29. APK & AAB](Q29-APK-AAB.md) - Android 패키징 포맷
- [Q30. R8 최적화](Q30-R8-최적화.md) - R8 코드 축소 및 최적화
- [Q31. App 크기 줄이기](Q31-App-크기-줄이기.md) - 앱 크기 최적화 전략
- [Q32. Android의 프로세스](Q32-Android의-프로세스.md) - Android 프로세스 관리
  - [Details: Android 4대 구성요소](Details-Android-4대-구성요소.md)

### 1.2 Android UI & Views

Android의 UI 시스템과 View 구성 요소를 다룹니다.

- [Q33. View Lifecycle](Q33-View-Lifecycle.md) - View의 생명주기
  - [Details: findViewTreeLifecycleOwner](Details-findViewTreeLifecycleOwner.md)
- [Q34. View & ViewGroup](Q34-View-ViewGroup.md) - View와 ViewGroup의 관계
- [Q35. ViewStub](Q35-ViewStub.md) - 지연 로딩을 위한 ViewStub
- [Q36. Custom View](Q36-Custom-View.md) - 커스텀 View 구현
  - [Details: 생성자 JvmOverloads](Details-생성자-JvmOverloads.md)
- [Q37. Canvas](Q37-Canvas.md) - View에 직접 그리기 위한 Canvas API
- [Q38. invalidate](Q38-invalidate.md) - View를 다시 그리도록 요청하기
- [Q39. ConstraintLayout](Q39-ConstraintLayout.md) - 유연한 제약 기반 레이아웃
- [Q40. SurfaceView & TextureView](Q40-SurfaceView-TextureView.md) - 고성능 렌더링용 View 컴포넌트
- [Q41. RecyclerView](Q41-RecyclerView.md) - 효율적인 리스트 렌더링을 위한 RecyclerView
  - [Details: Multiple Item Types](Details-Multiple-Item-Types.md)
  - [Details: DiffUtil](Details-DiffUtil.md)
- [Q42. Dp & Sp](Q42-Dp-Sp.md) - 화면 독립적 단위와 텍스트 크기 단위
  - [Details: Sp 사용 시 화면 깨짐 처리](Details-Sp-사용-시-화면-깨짐-처리.md)
- [Q43. nine-patch 이미지](Q43-nine-patch-이미지.md) - 신축 가능한 비트맵 이미지 포맷
- [Q44. Drawable](Q44-Drawable.md) - 그릴 수 있는 객체의 추상화
- [Q45. Bitmap](Q45-Bitmap.md) - 비트맵 이미지 처리와 메모리 관리
  - [Details: 대용량 Bitmap 캐싱](Details-대용량-Bitmap-캐싱.md)
- [Q46. 애니메이션](Q46-애니메이션.md) - Android의 애니메이션 시스템
  - [Details: 애니메이션 Interpolator](Details-애니메이션-Interpolator.md)
- [Q47. Window](Q47-Window.md) - Android Window 시스템 이해
  - [Details: WindowManager](Details-WindowManager.md)
  - [Details: PopupWindow](Details-PopupWindow.md)
- [Q48. WebView](Q48-WebView.md) - 앱 내 웹 콘텐츠 표시

### 1.3 Jetpack Library

Android Jetpack 라이브러리와 Architecture Components를 다룹니다.

- [Q49. AppCompat](Q49-AppCompat.md) - 하위 호환성을 위한 AppCompat
- [Q50. Material Design Components](Q50-Material-Design-Components.md) - 머티리얼 디자인 컴포넌트
- [Q51. ViewBinding](Q51-ViewBinding.md) - 타입 안전한 View 참조
- [Q52. DataBinding](Q52-DataBinding.md) - 선언적 데이터 바인딩
  - [Details: ViewBinding vs DataBinding](Details-ViewBinding-vs-DataBinding.md)
- [Q53. LiveData](Q53-LiveData.md) - 생명주기 인식 관찰 가능한 데이터 홀더
  - [Details: setValue vs postValue](Details-setValue-vs-postValue.md)
- [Q54. Jetpack ViewModel](Q54-JetPack-ViewModel.md) - ViewModel을 통한 UI 상태 관리
- [Q55. Jetpack Navigation Library](Q55-Jetpack-Navigation-Library.md) - 화면 간 탐색 관리
- [Q56. Dagger 2 & Hilt](Q56-Dagger-2-Hilt.md) - 의존성 주입 프레임워크
- [Q57. Jetpack Paging Library](Q57-Jetpack-Paging-Library.md) - 대용량 데이터셋 페이징
- [Q58. Baseline Profile](Q58-Baseline-Profile.md) - 시작 성능 향상을 위한 베이스라인 프로파일

### 1.4 Business Logic

비즈니스 로직과 데이터 처리 패턴을 다룹니다.

- [Q59. Long-running Background Tasks](Q59-Long-running-Background-Tasks.md) - 장기 실행 백그라운드 작업 처리
- [Q60. JSON Serialization](Q60-JSON-Serialization.md) - JSON 직렬화 라이브러리 비교
- [Q61. Network Requests](Q61-Network-Requests.md) - 네트워크 요청 처리 전략
  - [Details: OkHttp Authenticator vs Interceptor](Details-OkHttp-Authenticator-vs-Interceptor.md)
  - [Details: Retrofit CallAdapter](Details-Retrofit-CallAdapter.md)
- [Q62. Paging System for RecyclerView](Q62-Paging-System-RecyclerView.md) - RecyclerView 페이징 시스템 구현
- [Q63. Network Image Loading](Q63-Network-Image-Loading.md) - 네트워크 이미지 로딩 라이브러리
- [Q64. Local Data Persistence](Q64-Local-Data-Persistence.md) - 로컬 데이터 영속화 방법
- [Q65. Offline-First](Q65-Offline-First.md) - 오프라인 우선 아키텍처
- [Q66. 초기 데이터 로드 위치: LaunchedEffect vs. ViewModel.init()](Q66-초기-데이터-LaunchedEffect-vs-ViewModel-init.md) - 초기 데이터 로드 전략

### 2.1 Jetpack Compose

선언형 UI 프레임워크인 Jetpack Compose의 기초를 다룹니다.

- [Q0. Jetpack Compose 구조](Q0-Jetpack-Compose-구조.md) - Compose의 모듈 구성과 아키텍처
  - [Details: SlotTable & Link Table](Details-SlotTable-Link-Table.md)
- [Q1. Compose Phase](Q1-Compose-Phase.md) - Compose의 세 단계(Composition · Layout · Drawing)
- [Q2. Declarative UI](Q2-Declarative-UI.md) - 선언형 UI 패러다임 이해
- [Q3. Recomposition](Q3-Recomposition.md) - 상태 변경에 따른 UI 재구성
- [Q4. Composable Function Internals](Q4-Composable-Function-Internals.md) - Composable 함수의 내부 동작
  - [Details: Compose Compiler & Composer](Details-Compose-Compiler-Composer.md)
  - [Details: Composable Side-Effect Free](Details-Composable-Side-Effect-Free.md)
- [Q5. Stability](Q5-Stability.md) - Compose의 안정성 개념
  - [Details: Smart Recomposition](Details-Smart-Recomposition.md)
  - [Details: Stability Annotations](Details-Stability-Annotations.md)
  - [Details: Stable vs Immutable 오용](Details-Stable-vs-Immutable-Misuse.md)
- [Q6. Compose Stability Optimization](Q6-Compose-Stability-Optimization.md) - 안정성 기반 최적화 전략
- [Q7. Composition](Q7-Composition.md) - Composition의 개념과 동작 원리
- [Q8. XML → Compose Migration](Q8-XML-Compose-Migration.md) - XML 기반 코드의 Compose 전환
  - [Details: Compose 도입과 앱 크기](Details-Compose-XML-App-Size.md)
- [Q9. Release Mode Performance](Q9-Release-Mode-Performance.md) - 릴리즈 모드에서의 성능 차이
- [Q10. Kotlin Idioms](Q10-Kotlin-Idioms.md) - Compose에 자주 쓰이는 Kotlin 관용구

### 2.2 Compose Runtime

Compose의 런타임 동작과 상태 관리를 다룹니다.

- [Q11. State](Q11-State.md) - Compose의 상태 관리 시스템
- [Q12. State hoisting](Q12-State-hoisting.md) - 상태 끌어올리기 패턴
  - [Details: Stateful vs Stateless](Details-Stateful-vs-Stateless.md)
- [Q13. remember & rememberSaveable](Q13-remember-rememberSaveable.md) - 상태 저장 및 복원
- [Q14. rememberCoroutineScope](Q14-rememberCoroutineScope.md) - Compose에서 코루틴 사용하기
- [Q15. Side Effects](Q15-Side-Effects.md) - Compose의 부수효과 처리
- [Q16. rememberUpdatedState](Q16-rememberUpdatedState.md) - 변하는 람다를 안전하게 캡처하기
  - [Details: rememberUpdatedState 내부 구현](Details-rememberUpdatedState-내부-구현.md)
- [Q17. produceState](Q17-produceState.md) - 비동기 데이터를 State로 변환
  - [Details: produceState 내부 구현](Details-produceState-내부-구현.md)
- [Q18. snapshotFlow](Q18-snapshotFlow.md) - State를 Flow로 변환
- [Q19. derivedStateOf](Q19-derivedStateOf.md) - 다른 State에서 파생된 State 만들기
- [Q20. Composable Lifecycle](Q20-Composable-Lifecycle.md) - Composable 함수의 생명주기
- [Q21. SaveableStateHolder](Q21-SaveableStateHolder.md) - 화면 전환에서 상태 저장하기
- [Q22. Snapshot System](Q22-Snapshot-System.md) - Compose의 스냅샷 기반 상태 시스템
  - [Details: Mutable Snapshot](Details-Mutable-Snapshot.md)
- [Q23. mutableStateListOf, mutableStateMapOf](Q23-mutableStateListOf-mutableStateMapOf.md) - 관찰 가능한 컬렉션 상태
- [Q24. Flow Safe Collection](Q24-Flow-Safe-Collection.md) - Compose에서 Flow 안전하게 수집하기
- [Q25. CompositionLocals](Q25-CompositionLocals.md) - 암묵적 의존성 주입 메커니즘
  - [Details: CompositionLocal 사용 시 주의점](Details-CompositionLocal-Caution.md)

### 2.3 Compose UI

Compose UI 구성 요소와 레이아웃 시스템을 다룹니다.

- [Q26. Modifier](Q26-Modifier.md) - Compose에서 UI 요소 수정하기
- [Q27. Layout](Q27-Layout.md) - Compose의 Layout 시스템
  - [Details: SubcomposeLayout](Details-SubcomposeLayout.md)
- [Q28. Box](Q28-Box.md) - 자식들을 겹쳐 배치하는 컨테이너
  - [Details: BoxWithConstraints](Details-BoxWithConstraints.md)
- [Q29. Arrangement & Alignment](Q29-Arragement-Alignment.md) - Compose 레이아웃 정렬
- [Q30. Painter](Q30-Painter.md) - 그리기 동작을 추상화한 Painter API
- [Q31. Compose Network Image Loading](Q31-Compose-Network-Image-Loading.md) - Compose 네트워크 이미지 로딩
- [Q32. Lazy List Rendering](Q32-Lazy-List-Rendering.md) - LazyColumn · LazyRow의 렌더링 동작
- [Q33. Lazy List Pagination](Q33-Lazy-List-Pagination.md) - Lazy 리스트의 페이지네이션 구현
- [Q34. Compose Canvas](Q34-Compose-Canvas.md) - Compose에서의 직접 그리기
- [Q35. graphicsLayer](Q35-graphicsLayer.md) - 그래픽 변환과 레이어 효과
- [Q36. Compose Animations](Q36-Compose-Animations.md) - Compose 애니메이션 API
- [Q37. Compose Navigation](Q37-Compose-Navigation.md) - Compose에서의 화면 탐색
- [Q38. Compose Preview](Q38-Compose-Preview.md) - 컴포저블 프리뷰 활용
- [Q39. Compose UI Testing](Q39-Compose-UI-Testing.md) - Compose UI 단위 테스트
- [Q40. Screenshot Testing](Q40-Screenshot-Testing.md) - 스크린샷 기반 시각 회귀 테스트
- [Q41. Compose Accessibility](Q41-Compose-Accessibility.md) - Compose 접근성 보장하기

### 1.2 ETC

이 외로 추가적인 내용을 다룹니다.

- [E1. RecyclerView 렌더링 과정](E1-RecyclerView-렌더링-과정.md) - 효율적인 리스트 구현을 위한 RecyclerView
- [E2. Kotlin Flow](E2-Kotlin-Flow.md) - Kotlin의 비동기 데이터 스트림
- [E3. Kotlin Delegation](E3-Kotlin-Delegation.md) - Kotlin의 위임 패턴
- [E4. Thread Safe](E4-Thread-Safe.md) - 스레드 안전성 보장 기법
