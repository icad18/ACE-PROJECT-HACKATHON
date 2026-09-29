import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Enable CORS for frontend development
  app.enableCors({
    origin: 'http://localhost:3000', // Adjust this to your frontend URL
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
    credentials: true,
  });

  // Apply global validation pipe
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true, // Strips properties not defined in DTOs
    forbidNonWhitelisted: true, // Throws an error if non-whitelisted properties are present
    transform: true, // Automatically transform payloads to DTO instances
    transformOptions: {
      enableImplicitConversion: true, // Enable implicit type conversion
    },
  }));

  const port = process.env.PORT || 3001;
  await app.listen(port);
  console.log(`Application is running on: ${await app.getUrl()}`);
}
bootstrap();
