1. Backend Architecture Dökümanları
markdown


---
title: "FastAPI Project Structure"
category: "architecture"
tags: ["python", "fastapi", "backend", "api", "rest"]
difficulty: "intermediate"
importance: "high"
---

# FastAPI Project Structure

## Ne Zaman Kullanılır
- Python ile RESTful API geliştirirken
- Yüksek performanslı async backend gerektiğinde
- OpenAPI/Swagger dokümantasyonu otomatik oluşturulacaksa
- Type hints ile güvenli kod yazılacaksa

## Örnek Implementation

### Dizin Yapısı
project/ ├── app/ │ ├── init.py │ ├── main.py │ ├── config/ │ │ ├── init.py │ │ ├── settings.py │ │ └── database.py │ ├── models/ │ │ ├── init.py │ │ ├── user.py │ │ └── base.py │ ├── schemas/ │ │ ├── init.py │ │ ├── user.py │ │ └── common.py │ ├── api/ │ │ ├── init.py │ │ ├── deps.py │ │ └── v1/ │ │ ├── init.py │ │ ├── router.py │ │ └── endpoints/ │ │ ├── init.py │ │ ├── users.py │ │ └── auth.py │ ├── services/ │ │ ├── init.py │ │ ├── user_service.py │ │ └── auth_service.py │ ├── repositories/ │ │ ├── init.py │ │ └── user_repository.py │ └── core/ │ ├── init.py │ ├── security.py │ ├── exceptions.py │ └── middleware.py ├── tests/ ├── alembic/ ├── pyproject.toml ├── Dockerfile └── docker-compose.yml




### main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.api.v1.router import api_router
from app.core.middleware import LoggingMiddleware
from app.config.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=lifespan
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    
    # Routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    return app


app = create_app()
config/settings.py
python


from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "FastAPI App"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
Best Practices
Layered Architecture: Repository → Service → API katmanlarını ayır
Dependency Injection: FastAPI'nin Depends sistemini kullan
Pydantic Schemas: Request/Response için ayrı schema'lar oluştur
Async First: Tüm I/O operasyonlarında async kullan
Exception Handling: Global exception handler tanımla
Logging: Structured logging kullan (loguru/structlog)
Testing: Her endpoint için test yaz
Documentation: Docstring ve OpenAPI annotations kullan



---

```markdown
---
title: "Go Gin Project Structure"
category: "architecture"
tags: ["go", "golang", "gin", "backend", "api"]
difficulty: "intermediate"
importance: "high"
---

# Go Gin Project Structure

## Ne Zaman Kullanılır
- Yüksek performans gerektiren API'lerde
- Düşük memory footprint önemli olduğunda
- Concurrent işlemler yoğun olduğunda
- Microservices mimarisinde

## Örnek Implementation

### Dizin Yapısı
project/ ├── cmd/ │ └── api/ │ └── main.go ├── internal/ │ ├── config/ │ │ └── config.go │ ├── models/ │ │ ├── user.go │ │ └── base.go │ ├── handlers/ │ │ ├── user_handler.go │ │ └── auth_handler.go │ ├── services/ │ │ ├── user_service.go │ │ └── auth_service.go │ ├── repositories/ │ │ └── user_repository.go │ ├── middleware/ │ │ ├── auth.go │ │ ├── logging.go │ │ └── cors.go │ └── routes/ │ └── routes.go ├── pkg/ │ ├── database/ │ │ └── postgres.go │ ├── logger/ │ │ └── logger.go │ └── validator/ │ └── validator.go ├── migrations/ ├── go.mod ├── go.sum ├── Dockerfile └── Makefile




### cmd/api/main.go
```go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/gin-gonic/gin"
    "myapp/internal/config"
    "myapp/internal/routes"
    "myapp/pkg/database"
    "myapp/pkg/logger"
)

func main() {
    // Load config
    cfg, err := config.Load()
    if err != nil {
        log.Fatal("Failed to load config:", err)
    }

    // Initialize logger
    logger.Init(cfg.LogLevel)

    // Initialize database
    db, err := database.NewPostgres(cfg.DatabaseURL)
    if err != nil {
        log.Fatal("Failed to connect to database:", err)
    }
    defer db.Close()

    // Setup Gin
    if cfg.Environment == "production" {
        gin.SetMode(gin.ReleaseMode)
    }

    router := gin.New()
    router.Use(gin.Recovery())
    
    // Setup routes
    routes.Setup(router, db)

    // Server
    srv := &http.Server{
        Addr:         ":" + cfg.Port,
        Handler:      router,
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 15 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    // Graceful shutdown
    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatal("Server failed:", err)
        }
    }()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("Server forced to shutdown:", err)
    }
}
internal/handlers/user_handler.go
go


package handlers

import (
    "net/http"
    "strconv"

    "github.com/gin-gonic/gin"
    "myapp/internal/models"
    "myapp/internal/services"
)

type UserHandler struct {
    userService services.UserService
}

func NewUserHandler(us services.UserService) *UserHandler {
    return &UserHandler{userService: us}
}

func (h *UserHandler) GetUser(c *gin.Context) {
    id, err := strconv.ParseInt(c.Param("id"), 10, 64)
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
        return
    }

    user, err := h.userService.GetByID(c.Request.Context(), id)
    if err != nil {
        c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
        return
    }

    c.JSON(http.StatusOK, user)
}

func (h *UserHandler) CreateUser(c *gin.Context) {
    var req models.CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    user, err := h.userService.Create(c.Request.Context(), &req)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusCreated, user)
}

func (h *UserHandler) ListUsers(c *gin.Context) {
    page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
    limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))

    users, total, err := h.userService.List(c.Request.Context(), page, limit)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusOK, gin.H{
        "data":  users,
        "total": total,
        "page":  page,
        "limit": limit,
    })
}
Best Practices
Standard Layout: Go community standard project layout kullan
Interface-based Design: Service ve repository için interface tanımla
Context Propagation: Her fonksiyonda context kullan
Error Handling: Explicit error handling, panic kullanma
Graceful Shutdown: SIGTERM/SIGINT handle et
Structured Logging: zap veya zerolog kullan
Validation: go-playground/validator kullan
Testing: Table-driven tests yaz



---

```markdown
---
title: "NestJS Project Structure"
category: "architecture"
tags: ["nodejs", "nestjs", "typescript", "backend", "api"]
difficulty: "intermediate"
importance: "high"
---

# NestJS Project Structure

## Ne Zaman Kullanılır
- Enterprise-level Node.js uygulamalarında
- Angular benzeri modüler yapı istendiğinde
- TypeScript ile güçlü typing gerektiğinde
- Dependency Injection pattern kullanılacaksa

## Örnek Implementation

### Dizin Yapısı
project/ ├── src/ │ ├── main.ts │ ├── app.module.ts │ ├── common/ │ │ ├── decorators/ │ │ ├── filters/ │ │ ├── guards/ │ │ ├── interceptors/ │ │ └── pipes/ │ ├── config/ │ │ ├── config.module.ts │ │ └── configuration.ts │ ├── modules/ │ │ ├── auth/ │ │ │ ├── auth.module.ts │ │ │ ├── auth.controller.ts │ │ │ ├── auth.service.ts │ │ │ ├── strategies/ │ │ │ └── guards/ │ │ └── users/ │ │ ├── users.module.ts │ │ ├── users.controller.ts │ │ ├── users.service.ts │ │ ├── dto/ │ │ ├── entities/ │ │ └── repositories/ │ └── database/ │ ├── database.module.ts │ └── migrations/ ├── test/ ├── nest-cli.json ├── tsconfig.json ├── package.json └── Dockerfile




### src/main.ts
```typescript
import { NestFactory } from '@nestjs/core';
import { ValidationPipe, VersioningType } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { ConfigService } from '@nestjs/config';
import helmet from 'helmet';
import compression from 'compression';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    logger: ['error', 'warn', 'log', 'debug', 'verbose'],
  });

  const configService = app.get(ConfigService);

  // Security
  app.use(helmet());
  app.use(compression());
  
  // CORS
  app.enableCors({
    origin: configService.get('ALLOWED_ORIGINS')?.split(',') || '*',
    credentials: true,
  });

  // Versioning
  app.enableVersioning({
    type: VersioningType.URI,
    defaultVersion: '1',
  });

  // Global prefix
  app.setGlobalPrefix('api');

  // Validation
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );

  // Swagger
  if (configService.get('NODE_ENV') !== 'production') {
    const config = new DocumentBuilder()
      .setTitle('API Documentation')
      .setVersion('1.0')
      .addBearerAuth()
      .build();
    const document = SwaggerModule.createDocument(app, config);
    SwaggerModule.setup('docs', app, document);
  }

  // Graceful shutdown
  app.enableShutdownHooks();

  const port = configService.get('PORT') || 3000;
  await app.listen(port);
  console.log(`Application running on port ${port}`);
}

bootstrap();
src/modules/users/users.service.ts
typescript


import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';
import { PaginationDto } from '../../common/dto/pagination.dto';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}

  async create(createUserDto: CreateUserDto): Promise<User> {
    const user = this.userRepository.create(createUserDto);
    return this.userRepository.save(user);
  }

  async findAll(paginationDto: PaginationDto) {
    const { page = 1, limit = 10 } = paginationDto;
    const skip = (page - 1) * limit;

    const [data, total] = await this.userRepository.findAndCount({
      skip,
      take: limit,
      order: { createdAt: 'DESC' },
    });

    return {
      data,
      meta: {
        total,
        page,
        limit,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async findOne(id: number): Promise<User> {
    const user = await this.userRepository.findOne({ where: { id } });
    if (!user) {
      throw new NotFoundException(`User #${id} not found`);
    }
    return user;
  }

  async update(id: number, updateUserDto: UpdateUserDto): Promise<User> {
    const user = await this.findOne(id);
    Object.assign(user, updateUserDto);
    return this.userRepository.save(user);
  }

  async remove(id: number): Promise<void> {
    const user = await this.findOne(id);
    await this.userRepository.remove(user);
  }
}
Best Practices
Modular Architecture: Her feature için ayrı module oluştur
DTOs: Request/Response için DTO kullan
Entities: TypeORM entities ayrı dosyada tanımla
Guards & Interceptors: Cross-cutting concerns için kullan
Exception Filters: Global exception handling
Pipes: Validation ve transformation için
Testing: Her service için unit test yaz
Documentation: Swagger decorators kullan



---

## 2. Frontend Architecture Dökümanları

```markdown
---
title: "React Project Structure with TypeScript"
category: "architecture"
tags: ["react", "typescript", "frontend", "spa"]
difficulty: "intermediate"
importance: "high"
---

# React Project Structure with TypeScript

## Ne Zaman Kullanılır
- Modern SPA uygulamalarında
- Component-based UI geliştirmede
- Complex state management gerektiğinde
- Reusable component library oluştururken

## Örnek Implementation

### Dizin Yapısı (Feature-based)
src/ ├── app/ │ ├── App.tsx │ ├── router.tsx │ └── store.ts ├── features/ │ ├── auth/ │ │ ├── components/ │ │ │ ├── LoginForm.tsx │ │ │ └── RegisterForm.tsx │ │ ├── hooks/ │ │ │ └── useAuth.ts │ │ ├── services/ │ │ │ └── authApi.ts │ │ ├── store/ │ │ │ └── authSlice.ts │ │ ├── types/ │ │ │ └── auth.types.ts │ │ └── index.ts │ └── users/ │ ├── components/ │ ├── hooks/ │ ├── services/ │ └── store/ ├── shared/ │ ├── components/ │ │ ├── ui/ │ │ │ ├── Button/ │ │ │ │ ├── Button.tsx │ │ │ │ ├── Button.test.tsx │ │ │ │ ├── Button.styles.ts │ │ │ │ └── index.ts │ │ │ ├── Input/ │ │ │ ├── Modal/ │ │ │ └── index.ts │ │ └── layout/ │ │ ├── Header.tsx │ │ ├── Sidebar.tsx │ │ └── Footer.tsx │ ├── hooks/ │ │ ├── useLocalStorage.ts │ │ ├── useDebounce.ts │ │ └── useMediaQuery.ts │ ├── utils/ │ │ ├── cn.ts │ │ ├── formatters.ts │ │ └── validators.ts │ ├── types/ │ │ └── common.types.ts │ └── constants/ │ └── index.ts ├── services/ │ ├── api/ │ │ ├── client.ts │ │ └── interceptors.ts │ └── storage/ │ └── localStorage.ts ├── styles/ │ ├── globals.css │ └── variables.css └── main.tsx




### app/store.ts (Redux Toolkit)
```typescript
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import { authReducer } from '@/features/auth/store/authSlice';
import { apiSlice } from '@/services/api/apiSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    [apiSlice.reducerPath]: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }).concat(apiSlice.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
shared/components/ui/Button/Button.tsx
typescript


import { forwardRef, ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/shared/utils/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
features/auth/hooks/useAuth.ts
typescript


import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/app/store';
import { login, logout, selectAuth } from '../store/authSlice';
import { useLoginMutation, useLogoutMutation } from '../services/authApi';
import type { LoginCredentials } from '../types/auth.types';

export function useAuth() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading } = useAppSelector(selectAuth);
  
  const [loginMutation, { isLoading: isLoginLoading }] = useLoginMutation();
  const [logoutMutation] = useLogoutMutation();

  const handleLogin = useCallback(
    async (credentials: LoginCredentials) => {
      try {
        const result = await loginMutation(credentials).unwrap();
        dispatch(login(result));
        navigate('/dashboard');
        return { success: true };
      } catch (error) {
        return { success: false, error };
      }
    },
    [dispatch, loginMutation, navigate]
  );

  const handleLogout = useCallback(async () => {
    try {
      await logoutMutation().unwrap();
    } finally {
      dispatch(logout());
      navigate('/login');
    }
  }, [dispatch, logoutMutation, navigate]);

  return {
    user,
    isAuthenticated,
    isLoading: isLoading || isLoginLoading,
    login: handleLogin,
    logout: handleLogout,
  };
}
Best Practices
Feature-based Structure: İlgili dosyaları feature klasörlerinde grupla
Barrel Exports: Her klasörde index.ts ile export yönetimi
Custom Hooks: Business logic'i hooks içine al
Compound Components: Complex UI için compound pattern
Memoization: useMemo ve useCallback doğru kullan
Error Boundaries: Kritik bölgeleri sarmalı
Lazy Loading: Route-based code splitting
Testing: React Testing Library ile component test



---

```markdown
---
title: "Next.js 14 App Router Structure"
category: "architecture"
tags: ["nextjs", "react", "typescript", "ssr", "frontend"]
difficulty: "advanced"
importance: "high"
---

# Next.js 14 App Router Structure

## Ne Zaman Kullanılır
- SEO önemli web uygulamalarında
- SSR/SSG gerektiren projelerde
- Full-stack React uygulamalarında
- Edge runtime kullanılacaksa

## Örnek Implementation

### Dizin Yapısı
project/ ├── src/ │ ├── app/ │ │ ├── (auth)/ │ │ │ ├── login/ │ │ │ │ └── page.tsx │ │ │ ├── register/ │ │ │ │ └── page.tsx │ │ │ └── layout.tsx │ │ ├── (dashboard)/ │ │ │ ├── dashboard/ │ │ │ │ └── page.tsx │ │ │ ├── users/ │ │ │ │ ├── [id]/ │ │ │ │ │ └── page.tsx │ │ │ │ └── page.tsx │ │ │ └── layout.tsx │ │ ├── api/ │ │ │ ├── auth/ │ │ │ │ └── [...nextauth]/ │ │ │ │ └── route.ts │ │ │ └── users/ │ │ │ └── route.ts │ │ ├── layout.tsx │ │ ├── page.tsx │ │ ├── loading.tsx │ │ ├── error.tsx │ │ ├── not-found.tsx │ │ └── globals.css │ ├── components/ │ │ ├── ui/ │ │ ├── forms/ │ │ └── layouts/ │ ├── lib/ │ │ ├── auth.ts │ │ ├── db.ts │ │ └── utils.ts │ ├── hooks/ │ ├── services/ │ ├── types/ │ └── middleware.ts ├── public/ ├── prisma/ │ └── schema.prisma ├── next.config.js ├── tailwind.config.ts └── package.json




### src/app/layout.tsx
```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from '@/components/providers';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: {
    default: 'My App',
    template: '%s | My App',
  },
  description: 'Next.js 14 Application',
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
src/app/(dashboard)/users/page.tsx
typescript


import { Suspense } from 'react';
import { Metadata } from 'next';
import { UserList } from '@/components/users/UserList';
import { UserListSkeleton } from '@/components/users/UserListSkeleton';
import { getUsers } from '@/services/users';

export const metadata: Metadata = {
  title: 'Users',
  description: 'Manage users',
};

interface UsersPageProps {
  searchParams: {
    page?: string;
    search?: string;
  };
}

export default async function UsersPage({ searchParams }: UsersPageProps) {
  const page = Number(searchParams.page) || 1;
  const search = searchParams.search || '';

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Users</h1>
      
      <Suspense fallback={<UserListSkeleton />}>
        <UserListWrapper page={page} search={search} />
      </Suspense>
    </div>
  );
}

async function UserListWrapper({ 
  page, 
  search 
}: { 
  page: number; 
  search: string 
}) {
  const { users, totalPages } = await getUsers({ page, search });
  
  return (
    <UserList 
      users={users} 
      currentPage={page} 
      totalPages={totalPages} 
    />
  );
}
src/app/api/users/route.ts
typescript


import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { prisma } from '@/lib/db';

const createUserSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  role: z.enum(['user', 'admin']).default('user'),
});

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');
    const search = searchParams.get('search') || '';

    const where = search
      ? {
          OR: [
            { name: { contains: search, mode: 'insensitive' as const } },
            { email: { contains: search, mode: 'insensitive' as const } },
          ],
        }
      : {};

    const [users, total] = await Promise.all([
      prisma.user.findMany({
        where,
        skip: (page - 1) * limit,
        take: limit,
        orderBy: { createdAt: 'desc' },
        select: {
          id: true,
          name: true,
          email: true,
          role: true,
          createdAt: true,
        },
      }),
      prisma.user.count({ where }),
    ]);

    return NextResponse.json({
      users,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('GET /api/users error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session || session.user.role !== 'admin') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const body = await request.json();
    const validatedData = createUserSchema.parse(body);

    const existingUser = await prisma.user.findUnique({
      where: { email: validatedData.email },
    });

    if (existingUser) {
      return NextResponse.json(
        { error: 'Email already exists' },
        { status: 409 }
      );
    }

    const user = await prisma.user.create({
      data: validatedData,
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        createdAt: true,
      },
    });

    return NextResponse.json(user, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation Error', details: error.errors },
        { status: 400 }
      );
    }
    console.error('POST /api/users error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
src/middleware.ts
typescript


import { withAuth } from 'next-auth/middleware';
import { NextResponse } from 'next/server';

export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;
    const isAdminRoute = req.nextUrl.pathname.startsWith('/admin');
    
    if (isAdminRoute && token?.role !== 'admin') {
      return NextResponse.redirect(new URL('/dashboard', req.url));
    }
    
    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
  }
);

export const config = {
  matcher: ['/dashboard/:path*', '/admin/:path*', '/api/users/:path*'],
};
Best Practices
Route Groups: (folder) ile layout paylaşımı
Server Components: Default olarak server component kullan
Parallel Routes: @folder ile parallel data fetching
Intercepting Routes: (..)folder ile modal pattern
Server Actions: Form handling için use server
Streaming: loading.tsx ve Suspense ile
Caching: fetch cache ve revalidate stratejileri
Middleware: Auth ve redirect logic için



---

## 3. Infrastructure Dökümanları

```markdown
---
title: "Docker Multi-Stage Build Patterns"
category: "patterns"
tags: ["docker", "containerization", "devops", "optimization"]
difficulty: "intermediate"
importance: "high"
---

# Docker Multi-Stage Build Patterns

## Ne Zaman Kullanılır
- Production-ready container image oluştururken
- Image boyutunu minimize etmek istediğinde
- Build dependencies'i runtime'dan ayırmak için
- Security best practices uygulamak için

## Örnek Implementation

### Python FastAPI Dockerfile
```dockerfile
# ============================================================
# Stage 1: Builder
# ============================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Export requirements
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 2: Production
# ============================================================
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Copy application code
COPY --chown=appuser:appgroup ./app ./app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
Go Gin Dockerfile
dockerfile


# ============================================================
# Stage 1: Builder
# ============================================================
FROM golang:1.21-alpine as builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download && go mod verify

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s -X main.version=$(git describe --tags --always)" \
    -o /app/server ./cmd/api

# ============================================================
# Stage 2: Production
# ============================================================
FROM scratch as production

# Copy certificates and timezone data
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Copy binary
COPY --from=builder /app/server /server

# Set environment
ENV TZ=UTC

# Expose port
EXPOSE 8080

# Run
ENTRYPOINT ["/server"]
Node.js NestJS Dockerfile
dockerfile


# ============================================================
# Stage 1: Dependencies
# ============================================================
FROM node:20-alpine as deps

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm && \
    pnpm install --frozen-lockfile

# ============================================================
# Stage 2: Builder
# ============================================================
FROM node:20-alpine as builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build
RUN npm run build

# Prune dev dependencies
RUN npm prune --production

# ============================================================
# Stage 3: Production
# ============================================================
FROM node:20-alpine as production

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nestjs -u 1001

# Copy built application
COPY --from=builder --chown=nestjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nestjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nestjs:nodejs /app/package.json ./

# Set environment
ENV NODE_ENV=production

# Switch to non-root user
USER nestjs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Expose port
EXPOSE 3000

# Run
CMD ["node", "dist/main"]
Best Practices
Multi-stage Builds: Build ve runtime ayrı stage'lerde
Non-root User: Container'ı root olmadan çalıştır
Minimal Base Image: alpine veya distroless kullan
Layer Caching: Sık değişen dosyaları en sona koy
Health Checks: HEALTHCHECK instruction ekle
Security Scanning: trivy veya snyk ile scan
.dockerignore: Gereksiz dosyaları exclude et
Labels: Metadata için label ekle



---

```markdown
---
title: "Kubernetes Deployment Patterns"
category: "patterns"
tags: ["kubernetes", "k8s", "deployment", "devops"]
difficulty: "advanced"
importance: "high"
---

# Kubernetes Deployment Patterns

## Ne Zaman Kullanılır
- Container orchestration gerektiğinde
- High availability ve auto-scaling için
- Microservices deployment'ta
- Production workload yönetiminde

## Örnek Implementation

### Complete Application Deployment
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: myapp
  labels:
    name: myapp
    environment: production

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
  namespace: myapp
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  DB_HOST: "postgres-service"
  REDIS_HOST: "redis-service"

---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
  namespace: myapp
type: Opaque
stringData:
  DB_PASSWORD: "changeme"
  JWT_SECRET: "your-jwt-secret"
  API_KEY: "your-api-key"

---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-api
  namespace: myapp
  labels:
    app: myapp-api
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: myapp-api
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: myapp-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: api
          image: myapp/api:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8080
              name: http
          envFrom:
            - configMapRef:
                name: myapp-config
            - secretRef:
                name: myapp-secrets
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: myapp-api
                topologyKey: kubernetes.io/hostname
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: myapp-api

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-api-service
  namespace: myapp
  labels:
    app: myapp-api
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
      name: http
  selector:
    app: myapp-api

---
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-api-hpa
  namespace: myapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  namespace: myapp
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.example.com
      secretName: myapp-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-api-service
                port:
                  number: 80

---
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-api-pdb
  namespace: myapp
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: myapp-api

---
# networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: myapp-api-network-policy
  namespace: myapp
spec:
  podSelector:
    matchLabels:
      app: myapp-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
        - podSelector:
            matchLabels:
              app: myapp-frontend
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 5432
        - protocol: TCP
          port: 6379
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
Best Practices
Resource Limits: Her container için CPU/memory limit tanımla
Health Probes: Liveness ve readiness probe kullan
Security Context: Non-root, read-only filesystem
Pod Disruption Budget: Minimum availability garanti et
Network Policies: Traffic isolation uygula
HPA: Auto-scaling için metric-based HPA
Pod Anti-affinity: Pod'ları farklı node'lara dağıt
Topology Spread: Zone'lar arası dengeleme



---

```markdown
---
title: "Terraform AWS Infrastructure"
category: "solutions"
tags: ["terraform", "aws", "iac", "infrastructure"]
difficulty: "advanced"
importance: "high"
---

# Terraform AWS Infrastructure

## Ne Zaman Kullanılır
- AWS altyapısı kod olarak yönetilecekse
- Reproducible infrastructure gerektiğinde
- Multi-environment deployment'ta
- Team collaboration ile infrastructure yönetiminde

## Örnek Implementation

### Dizin Yapısı
terraform/ ├── modules/ │ ├── vpc/ │ │ ├── main.tf │ │ ├── variables.tf │ │ └── outputs.tf │ ├── eks/ │ ├── rds/ │ └── elasticache/ ├── environments/ │ ├── dev/ │ │ ├── main.tf │ │ ├── variables.tf │ │ ├── terraform.tfvars │ │ └── backend.tf │ ├── staging/ │ └── production/ └── global/ └── iam/




### modules/vpc/main.tf
```hcl
# VPC Module

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 3)
  
  tags = merge(var.tags, {
    Module    = "vpc"
    ManagedBy = "terraform"
  })
}

data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, {
    Name = "${var.environment}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.tags, {
    Name = "${var.environment}-igw"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = length(local.azs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.tags, {
    Name                        = "${var.environment}-public-${local.azs[count.index]}"
    "kubernetes.io/role/elb"    = "1"
    "kubernetes.io/cluster/${var.environment}" = "shared"
  })
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = length(local.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(local.azs))
  availability_zone = local.azs[count.index]

  tags = merge(local.tags, {
    Name                              = "${var.environment}-private-${local.azs[count.index]}"
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${var.environment}" = "shared"
  })
}

# Database Subnets
resource "aws_subnet" "database" {
  count             = length(local.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 2 * length(local.azs))
  availability_zone = local.azs[count.index]

  tags = merge(local.tags, {
    Name = "${var.environment}-database-${local.azs[count.index]}"
  })
}

# NAT Gateway
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(local.azs)) : 0
  domain = "vpc"

  tags = merge(local.tags, {
    Name = "${var.environment}-nat-eip-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(local.azs)) : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(local.tags, {
    Name = "${var.environment}-nat-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.tags, {
    Name = "${var.environment}-public-rt"
  })
}

resource "aws_route_table" "private" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(local.azs)) : 1
  vpc_id = aws_vpc.main.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
    }
  }

  tags = merge(local.tags, {
    Name = "${var.environment}-private-rt-${count.index + 1}"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = var.single_nat_gateway ? aws_route_table.private[0].id : aws_route_table.private[count.index].id
}

# VPC Flow Logs
resource "aws_flow_log" "main" {
  count                = var.enable_flow_logs ? 1 : 0
  iam_role_arn         = aws_iam_role.flow_logs[0].arn
  log_destination      = aws_cloudwatch_log_group.flow_logs[0].arn
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.main.id
  max_aggregation_interval = 60

  tags = merge(local.tags, {
    Name = "${var.environment}-vpc-flow-logs"
  })
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  count             = var.enable_flow_logs ? 1 : 0
  name              = "/aws/vpc/${var.environment}/flow-logs"
  retention_in_days = 30

  tags = local.tags
}

resource "aws_iam_role" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0
  name  = "${var.environment}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy" "flow_logs" {
  count = var.enable_flow_logs ? 1 : 0
  name  = "${var.environment}-vpc-flow-logs-policy"
  role  = aws_iam_role.flow_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}
modules/vpc/variables.tf
hcl


variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
modules/vpc/outputs.tf
hcl


output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "Database subnet IDs"
  value       = aws_subnet.database[*].id
}

output "nat_gateway_ips" {
  description = "NAT Gateway public IPs"
  value       = aws_eip.nat[*].public_ip
}
environments/production/main.tf
hcl


terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  }
}

module "vpc" {
  source = "../../modules/vpc"

  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  enable_nat_gateway = true
  single_nat_gateway = false
  enable_flow_logs   = true

  tags = var.tags
}

module "eks" {
  source = "../../modules/eks"

  environment        = var.environment
  cluster_name       = "${var.project_name}-${var.environment}"
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  kubernetes_version = var.kubernetes_version

  node_groups = {
    general = {
      instance_types = ["t3.large"]
      min_size       = 2
      max_size       = 10
      desired_size   = 3
    }
  }

  tags = var.tags
}

module "rds" {
  source = "../../modules/rds"

  environment          = var.environment
  identifier           = "${var.project_name}-${var.environment}"
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.database_subnet_ids
  allowed_security_groups = [module.eks.node_security_group_id]
  
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.r6g.large"
  allocated_storage    = 100
  multi_az             = true
  
  database_name        = var.database_name
  master_username      = var.database_username

  tags = var.tags
}

module "elasticache" {
  source = "../../modules/elasticache"

  environment         = var.environment
  cluster_id          = "${var.project_name}-${var.environment}"
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  allowed_security_groups = [module.eks.node_security_group_id]
  
  engine              = "redis"
  node_type           = "cache.r6g.large"
  num_cache_nodes     = 2
  
  tags = var.tags
}
Best Practices
Module Structure: Reusable module'lar oluştur
Remote State: S3 + DynamoDB ile state yönetimi
Workspaces vs Directories: Environment ayrımı için directory kullan
Variable Validation: Input validation ekle
Outputs: Gerekli değerleri output olarak expose et
Tagging Strategy: Tutarlı tagging uygula
Security: Sensitive variables için encryption
Documentation: Her module için README yaz



---

## 4. CI/CD Dökümanları

```markdown
---
title: "GitHub Actions CI/CD Pipeline"
category: "solutions"
tags: ["github-actions", "cicd", "automation", "devops"]
difficulty: "intermediate"
importance: "high"
---

# GitHub Actions CI/CD Pipeline

## Ne Zaman Kullanılır
- GitHub repository'leri için CI/CD
- Automated testing ve deployment
- Multi-environment deployment stratejileri
- Container-based deployments

## Örnek Implementation

### Complete CI/CD Workflow
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  release:
    types: [published]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

permissions:
  contents: read
  packages: write
  security-events: write

jobs:
  # ============================================
  # Lint & Static Analysis
  # ============================================
  lint:
    name: Lint & Static Analysis
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install ruff mypy

      - name: Run Ruff
        run: ruff check .

      - name: Run MyPy
        run: mypy . --ignore-missing-imports

  # ============================================
  # Security Scan
  # ============================================
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run Snyk
        uses: snyk/actions/python@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  # ============================================
  # Unit Tests
  # ============================================
  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install UV
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379
        run: |
          uv run pytest tests/ \
            --cov=app \
            --cov-report=xml \
            --cov-report=html \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          token: ${{ secrets.CODECOV_TOKEN }}

  # ============================================
  # Build & Push
  # ============================================
  build:
    name: Build & Push
    runs-on: ubuntu-latest
    needs: [lint, test, security]
    if: github.event_name != 'pull_request'
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
      image_digest: ${{ steps.build.outputs.digest }}
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=sha,prefix=

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

      - name: Sign image
        env:
          COSIGN_PRIVATE_KEY: ${{ secrets.COSIGN_PRIVATE_KEY }}
          COSIGN_PASSWORD: ${{ secrets.COSIGN_PASSWORD }}
        run: |
          cosign sign --yes --key env://COSIGN_PRIVATE_KEY \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build.outputs.digest }}

  # ============================================
  # Deploy to Staging
  # ============================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build]
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.example.com
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name staging-cluster --region us-east-1

      - name: Deploy to Kubernetes
        run: |
          helm upgrade --install myapp ./helm/myapp \
            --namespace staging \
            --create-namespace \
            --set image.tag=${{ github.sha }} \
            --set environment=staging \
            --values ./helm/values-staging.yaml \
            --wait \
            --timeout 10m

      - name: Run smoke tests
        run: |
          kubectl wait --for=condition=ready pod \
            -l app=myapp \
            -n staging \
            --timeout=300s
          
          curl -f https://staging.example.com/health || exit 1

  # ============================================
  # Deploy to Production
  # ============================================
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build]
    if: github.event_name == 'release'
    environment:
      name: production
      url: https://example.com
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name production-cluster --region us-east-1

      - name: Deploy with Blue-Green
        run: |
          # Get current deployment color
          CURRENT_COLOR=$(kubectl get svc myapp-active -n production -o jsonpath='{.spec.selector.color}' || echo "blue")
          NEW_COLOR=$([ "$CURRENT_COLOR" == "blue" ] && echo "green" || echo "blue")
          
          # Deploy new version
          helm upgrade --install myapp-$NEW_COLOR ./helm/myapp \
            --namespace production \
            --set image.tag=${{ github.event.release.tag_name }} \
            --set color=$NEW_COLOR \
            --set environment=production \
            --values ./helm/values-production.yaml \
            --wait \
            --timeout 15m
          
          # Run tests against new deployment
          kubectl wait --for=condition=ready pod \
            -l app=myapp,color=$NEW_COLOR \
            -n production \
            --timeout=300s
          
          # Switch traffic
          kubectl patch svc myapp-active -n production \
            -p "{\"spec\":{\"selector\":{\"color\":\"$NEW_COLOR\"}}}"
          
          echo "Deployed $NEW_COLOR successfully"

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚀 Production deployment completed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Production Deployment Completed*\nVersion: ${{ github.event.release.tag_name }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
Best Practices
Job Dependencies: needs ile dependency chain oluştur
Caching: Docker layer cache ve dependency cache kullan
Secrets Management: GitHub Secrets kullan
Environment Protection: Manual approval ekle
Matrix Builds: Multiple versions/platforms test et
Reusable Workflows: Common logic'i reusable workflow yap
Artifact Signing: Container image'ları sign et
Notifications: Slack/Teams notification ekle



---

## 5. Database Patterns

```markdown
---
title: "PostgreSQL Schema Design Patterns"
category: "patterns"
tags: ["postgresql", "database", "schema", "sql"]
difficulty: "intermediate"
importance: "high"
---

# PostgreSQL Schema Design Patterns

## Ne Zaman Kullanılır
- Relational database tasarımında
- Complex data modeling gerektiren projelerde
- Performance optimization için
- Multi-tenant uygulamalarda

## Örnek Implementation

### Base Schema with Audit
```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Base audit columns function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    email_verified_at TIMESTAMPTZ,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_login_at TIMESTAMPTZ,
    login_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'moderator', 'user')),
    CONSTRAINT users_status_check CHECK (status IN ('active', 'inactive', 'suspended', 'pending'))
);

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Indexes
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Organizations (Multi-tenant)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    domain VARCHAR(255),
    logo_url TEXT,
    settings JSONB DEFAULT '{}',
    billing_email VARCHAR(255),
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    trial_ends_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT organizations_plan_check CHECK (plan IN ('free', 'starter', 'professional', 'enterprise'))
);

CREATE TRIGGER organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Organization memberships
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    permissions JSONB DEFAULT '[]',
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMPTZ,
    joined_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, user_id),
    CONSTRAINT org_members_role_check CHECK (role IN ('owner', 'admin', 'member', 'viewer'))
);

CREATE INDEX idx_org_members_org ON organization_members(organization_id);
CREATE INDEX idx_org_members_user ON organization_members(user_id);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',
    settings JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    
    UNIQUE(organization_id, slug),
    CONSTRAINT projects_status_check CHECK (status IN ('active', 'archived', 'deleted')),
    CONSTRAINT projects_visibility_check CHECK (visibility IN ('private', 'internal', 'public'))
);

CREATE INDEX idx_projects_org ON projects(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_status ON projects(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_created_by ON projects(created_by);

-- Audit log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create partitions for audit logs (monthly)
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE audit_logs_2024_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Create index on partitioned table
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id, created_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- Row Level Security
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY projects_org_isolation ON projects
    USING (organization_id = current_setting('app.current_org_id')::UUID);

-- Functions for common queries
CREATE OR REPLACE FUNCTION get_user_organizations(p_user_id UUID)
RETURNS TABLE (
    organization_id UUID,
    organization_name VARCHAR(255),
    user_role VARCHAR(50),
    member_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.name,
        om.role,
        (SELECT COUNT(*) FROM organization_members WHERE organization_id = o.id)
    FROM organizations o
    JOIN organization_members om ON o.id = om.organization_id
    WHERE om.user_id = p_user_id
    AND o.deleted_at IS NULL
    ORDER BY o.name;
END;
$$ LANGUAGE plpgsql STABLE;

-- Materialized view for analytics
CREATE MATERIALIZED VIEW organization_stats AS
SELECT 
    o.id AS organization_id,
    o.name AS organization_name,
    COUNT(DISTINCT om.user_id) AS member_count,
    COUNT(DISTINCT p.id) AS project_count,
    o.plan,
    o.created_at
FROM organizations o
LEFT JOIN organization_members om ON o.id = om.organization_id
LEFT JOIN projects p ON o.id = p.organization_id AND p.deleted_at IS NULL
WHERE o.deleted_at IS NULL
GROUP BY o.id, o.name, o.plan, o.created_at;

CREATE UNIQUE INDEX idx_org_stats_id ON organization_stats(organization_id);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_organization_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY organization_stats;
END;
$$ LANGUAGE plpgsql;
Best Practices
UUID Primary Keys: Auto-increment yerine UUID kullan
Soft Deletes: deleted_at ile soft delete pattern
Audit Columns: created_at, updated_at, deleted_at
Check Constraints: Data integrity için constraint kullan
Indexes: Query pattern'e göre index oluştur
Partitioning: Büyük tablolar için partitioning
RLS: Multi-tenant için Row Level Security
Materialized Views: Complex aggregate'ler için



---

## 6. Testing Patterns

```markdown
---
title: "Comprehensive Testing Patterns"
category: "best_practices"
tags: ["testing", "pytest", "jest", "tdd", "quality"]
difficulty: "intermediate"
importance: "high"
---

# Comprehensive Testing Patterns

## Ne Zaman Kullanılır
- Quality assurance için
- Regression prevention
- Documentation as tests
- Refactoring güvenliği için

## Örnek Implementation

### Python pytest Patterns
```python
# tests/conftest.py
import pytest
from typing import Generator, AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config.database import get_db
from app.models.base import Base


# Test database
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test"""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def user_factory(db_session):
    """Factory for creating test users"""
    async def create_user(**kwargs):
        from app.models.user import User
        
        defaults = {
            "email": f"test_{uuid4().hex[:8]}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "hashed_password",
            "role": "user",
            "status": "active",
        }
        defaults.update(kwargs)
        
        user = User(**defaults)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    return create_user


@pytest.fixture
async def authenticated_client(client, user_factory):
    """Client with authentication"""
    user = await user_factory()
    
    # Get auth token
    response = await client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": "password123"
    })
    token = response.json()["access_token"]
    
    client.headers["Authorization"] = f"Bearer {token}"
    client.user = user
    
    return client


# tests/api/test_users.py
import pytest
from uuid import uuid4


class TestUserEndpoints:
    """Tests for user endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, client):
        """Test successful user creation"""
        # Arrange
        user_data = {
            "email": f"new_{uuid4().hex[:8]}@example.com",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        # Act
        response = await client.post("/api/v1/users", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client, user_factory):
        """Test error when creating user with existing email"""
        # Arrange
        existing_user = await user_factory()
        user_data = {
            "email": existing_user.email,
            "password": "SecurePass123!",
            "first_name": "Jane",
            "last_name": "Doe"
        }
        
        # Act
        response = await client.post("/api/v1/users", json=user_data)
        
        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, client):
        """Test validation error for invalid email"""
        # Arrange
        user_data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        # Act
        response = await client.post("/api/v1/users", json=user_data)
        
        # Assert
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_user_success(self, authenticated_client, user_factory):
        """Test getting user by ID"""
        # Arrange
        user = await user_factory()
        
        # Act
        response = await authenticated_client.get(f"/api/v1/users/{user.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["email"] == user.email
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, authenticated_client):
        """Test 404 for non-existent user"""
        # Act
        response = await authenticated_client.get(f"/api/v1/users/{uuid4()}")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_users_pagination(self, authenticated_client, user_factory):
        """Test user list pagination"""
        # Arrange
        for _ in range(15):
            await user_factory()
        
        # Act
        response = await authenticated_client.get(
            "/api/v1/users",
            params={"page": 1, "limit": 10}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["meta"]["total"] >= 15
        assert data["meta"]["page"] == 1
        assert data["meta"]["limit"] == 10
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("role,expected_status", [
        ("admin", 200),
        ("user", 403),
        ("viewer", 403),
    ])
    async def test_delete_user_permissions(
        self, 
        client, 
        user_factory, 
        role, 
        expected_status
    ):
        """Test delete permissions by role"""
        # Arrange
        admin = await user_factory(role=role)
        target = await user_factory()
        
        # Authenticate as admin
        response = await client.post("/api/v1/auth/login", json={
            "email": admin.email,
            "password": "password123"
        })
        token = response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Act
        response = await client.delete(f"/api/v1/users/{target.id}")
        
        # Assert
        assert response.status_code == expected_status


# tests/services/test_user_service.py
import pytest
from unittest.mock import AsyncMock, patch

from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class TestUserService:
    """Unit tests for UserService"""
    
    @pytest.fixture
    def mock_repository(self):
        return AsyncMock(spec=UserRepository)
    
    @pytest.fixture
    def service(self, mock_repository):
        return UserService(repository=mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_user_hashes_password(self, service, mock_repository):
        """Test that password is hashed before saving"""
        # Arrange
        user_data = UserCreate(
            email="test@example.com",
            password="plaintext123",
            first_name="Test",
            last_name="User"
        )
        mock_repository.get_by_email.return_value = None
        mock_repository.create.return_value = AsyncMock(id="123")
        
        # Act
        with patch("app.services.user_service.hash_password") as mock_hash:
            mock_hash.return_value = "hashed_password"
            await service.create_user(user_data)
        
        # Assert
        mock_hash.assert_called_once_with("plaintext123")
        create_call = mock_repository.create.call_args
        assert create_call[1]["password_hash"] == "hashed_password"
        assert "password" not in create_call[1]
    
    @pytest.mark.asyncio
    async def test_create_user_raises_on_duplicate_email(
        self, 
        service, 
        mock_repository
    ):
        """Test error raised for duplicate email"""
        # Arrange
        user_data = UserCreate(
            email="existing@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        mock_repository.get_by_email.return_value = AsyncMock(id="existing")
        
        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            await service.create_user(user_data)
        
        mock_repository.create.assert_not_called()
Best Practices
AAA Pattern: Arrange-Act-Assert yapısı kullan
Fixtures: Test data için fixture kullan
Factories: Dynamic test data için factory pattern
Parametrize: Multiple case'ler için parametrize
Mocking: External dependencies mock'la
Isolation: Her test bağımsız olmalı
Naming: Descriptive test isimleri kullan
Coverage: Critical path'leri mutlaka kapsa



---

## 7. Security Patterns

```markdown
---
title: "Security Best Practices"
category: "best_practices"
tags: ["security", "authentication", "authorization", "jwt"]
difficulty: "advanced"
importance: "high"
---

# Security Best Practices

## Ne Zaman Kullanılır
- User authentication gerektiren uygulamalarda
- Sensitive data koruması için
- API security sağlamak için
- Compliance gereksinimleri karşılamak için

## Örnek Implementation

### JWT Authentication with Refresh Tokens
```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
import secrets

from app.config.settings import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    iat: datetime
    jti: str
    type: str  # "access" or "refresh"


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    subject: str,
    token_type: str,
    expires_delta: Optional[timedelta] = None
) -> Tuple[str, datetime, str]:
    """Create JWT token"""
    now = datetime.utcnow()
    jti = secrets.token_urlsafe(32)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES 
            if token_type == "access" 
            else settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        )
    
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": token_type
    }
    
    token = jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return token, expire, jti


def create_access_token(subject: str) -> Tuple[str, datetime]:
    """Create access token"""
    token, expire, _ = create_token(
        subject, 
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return token, expire


def create_refresh_token(subject: str) -> Tuple[str, datetime, str]:
    """Create refresh token"""
    return create_token(
        subject, 
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return TokenPayload(**payload)
    except JWTError:
        return None


# app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.core.security import decode_token
from app.models.user import User
from app.services.user_service import UserService
from app.services.token_service import TokenService


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(),
    token_service: TokenService = Depends()
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check token type
    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Check if token is blacklisted
    if await token_service.is_blacklisted(payload.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    # Get user
    user = await user_service.get_by_id(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return user


def require_role(*roles: str):
    """Require specific role(s)"""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return role_checker


# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasicCredentials
from datetime import datetime

from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    RefreshRequest, 
    RefreshResponse
)
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.rate_limit import rate_limit


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
@rate_limit(requests=5, window=60)  # 5 requests per minute
async def login(
    request: Request,
    credentials: LoginRequest,
    auth_service: AuthService = Depends(),
    token_service: TokenService = Depends()
):
    """Authenticate user and return tokens"""
    # Get user
    user = await auth_service.get_user_by_email(credentials.email)
    if not user:
        # Use constant time comparison to prevent timing attacks
        verify_password("dummy", "\$2b\$12$dummy.hash.to.prevent.timing.attacks")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        # Log failed attempt
        await auth_service.log_failed_attempt(
            user_id=user.id,
            ip_address=request.client.host
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if account is locked
    if await auth_service.is_account_locked(user.id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked"
        )
    
    # Create tokens
    access_token, access_exp = create_access_token(str(user.id))
    refresh_token, refresh_exp, jti = create_refresh_token(str(user.id))
    
    # Store refresh token
    await token_service.store_refresh_token(
        user_id=user.id,
        jti=jti,
        expires_at=refresh_exp,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    # Update last login
    await auth_service.update_last_login(user.id)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int((access_exp - datetime.utcnow()).total_seconds())
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    token_service: TokenService = Depends()
):
    """Refresh access token"""
    # Decode refresh token
    payload = decode_token(body.refresh_token)
    if not payload or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify refresh token exists and is valid
    stored_token = await token_service.get_refresh_token(payload.jti)
    if not stored_token or stored_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    # Create new access token
    access_token, access_exp = create_access_token(payload.sub)
    
    # Optionally rotate refresh token
    new_refresh_token = None
    if settings.ROTATE_REFRESH_TOKENS:
        # Revoke old refresh token
        await token_service.revoke_refresh_token(payload.jti)
        
        # Create new refresh token
        new_refresh_token, refresh_exp, new_jti = create_refresh_token(payload.sub)
        await token_service.store_refresh_token(
            user_id=payload.sub,
            jti=new_jti,
            expires_at=refresh_exp,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
    
    return RefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=int((access_exp - datetime.utcnow()).total_seconds())
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: TokenService = Depends()
):
    """Logout user and revoke tokens"""
    payload = decode_token(credentials.credentials)
    if payload:
        # Blacklist access token
        await token_service.blacklist_token(
            payload.jti, 
            payload.exp
        )
        
        # Revoke all refresh tokens for user
        await token_service.revoke_all_refresh_tokens(payload.sub)
    
    return {"message": "Successfully logged out"}