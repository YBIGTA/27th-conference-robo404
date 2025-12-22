cmake_minimum_required(VERSION 3.8)
project(my_robot_bringup)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 의존성 찾기 (사실 이 패키지는 코드 빌드가 없어서 필수적이진 않음)
find_package(ament_cmake REQUIRED)

# launch, maps, worlds 폴더를 설치 경로로 복사
install(DIRECTORY
  launch maps worlds models
  DESTINATION share/${PROJECT_NAME}
)

install(FILES
  package.xml
  DESTINATION share/${PROJECT_NAME}
)

ament_package()