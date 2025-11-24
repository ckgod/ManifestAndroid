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

### 1.3 Jetpack Library

Android Jetpack 라이브러리와 Architecture Components를 다룹니다.

- [Q54. Jetpack ViewModel](Q54-JetPack-ViewModel.md) - ViewModel을 통한 UI 상태 관리
- [Q56. Dagger 2 & Hilt](Q56-Dagger-2-Hilt.md) - 의존성 주입 프레임워크

### 1.4 Business Logic

비즈니스 로직과 데이터 처리 패턴을 다룹니다.

- [Q66. 초기 데이터 로드 위치: LaunchedEffect vs. ViewModel.init()](Q66-초기-데이터-LaunchedEffect-vs-ViewModel-init.md) - 초기 데이터 로드 전략

### 2.1 Jetpack Compose

선언형 UI 프레임워크인 Jetpack Compose의 기초를 다룹니다.

### 2.2 Compose Runtime

Compose의 런타임 동작과 상태 관리를 다룹니다.

- [Q11. State](Q11-State.md) - Compose의 상태 관리 시스템
- [Q12. State hoisting](Q12-State-hoisting.md) - 상태 끌어올리기 패턴
  - [Details: Stateful vs Stateless](Details-Stateful-vs-Stateless.md)
- [Q13. remember & rememberSaveable](Q13-remember-rememberSaveable.md) - 상태 저장 및 복원
- [Q14. rememberCoroutineScope](Q14-rememberCoroutineScope.md) - Compose에서 코루틴 사용하기
- [Q15. Side Effects](Q15-Side-Effects.md) - Compose의 부수효과 처리
- [Q20. Composable Lifecycle](Q20-Composable-Lifecycle.md) - Composable 함수의 생명주기

### 2.3 Compose UI

Compose UI 구성 요소와 레이아웃 시스템을 다룹니다.

- [Q26. Modifier](Q26-Modifier.md) - Compose에서 UI 요소 수정하기
- [Q29. Arrangement & Alignment](Q29-Arragement-Alignment.md) - Compose 레이아웃 정렬

### 1.2 ETC

이 외로 추가적인 내용을 다룹니다.

- [E1. RecyclerView 렌더링 과정](E1-RecyclerView-렌더링-과정.md) - 효율적인 리스트 구현을 위한 RecyclerView
- [E2. Kotlin Flow](E2-Kotlin-Flow.md) - Kotlin의 비동기 데이터 스트림
- [E3. Kotlin Delegation](E3-Kotlin-Delegation.md) - Kotlin의 위임 패턴
